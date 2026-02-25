from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class SheetSelection:
    sheet_name: str | int
    header_row: Optional[int]


class ExcelReader:
    """
    Production XLSX/XLS reader with deterministic selection logic.

    Features:
    - openpyxl-first strategy for modern formats
    - fallback engine attempts
    - auto sheet detection
    - dynamic header row scan
    - loud and actionable failures
    """

    @staticmethod
    def read(
        file_path: str,
        sheet_name: str | int | None = "auto",
        header: int | None | str = "auto",
        detect_dates: bool = True,
    ) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        suffix = path.suffix.lower()
        if suffix not in {".xlsx", ".xls", ".xlsm", ".xltx"}:
            raise ValueError(f"Unsupported Excel format '{suffix}' for file: {path}")

        selection: Optional[SheetSelection] = None
        last_error: Optional[Exception] = None

        for engine in ExcelReader._engine_candidates(suffix):
            try:
                selection = ExcelReader._resolve_selection(
                    path=path,
                    engine=engine,
                    requested_sheet=sheet_name,
                    requested_header=header,
                )
                df = pd.read_excel(
                    str(path),
                    sheet_name=selection.sheet_name,
                    header=selection.header_row,
                    engine=engine,
                )
                df = df.dropna(how="all").reset_index(drop=True)
                if df.empty:
                    raise ValueError(
                        f"Selected sheet '{selection.sheet_name}' is empty after cleanup."
                    )

                if selection.header_row is not None:
                    df.columns = ExcelReader._normalize_columns(df.columns)

                if detect_dates and selection.header_row is not None:
                    ExcelReader._validate_temporal_columns(df, selection.sheet_name)

                return df
            except PermissionError as exc:
                raise RuntimeError(
                    f"Excel file is locked or not accessible: {path}. "
                    "Close it in other applications and retry."
                ) from exc
            except Exception as exc:
                last_error = exc
                continue

        if suffix == ".xls":
            raise RuntimeError(
                f"Failed to read '{path}'. Legacy .xls files may require xlrd. "
                "Install xlrd or convert the file to .xlsx."
            ) from last_error

        raise RuntimeError(
            f"Failed to read Excel file '{path}'. "
            "Tried openpyxl and pandas auto-engine fallback."
        ) from last_error

    @staticmethod
    def _resolve_selection(
        path: Path,
        engine: Optional[str],
        requested_sheet: str | int | None,
        requested_header: int | None | str,
    ) -> SheetSelection:
        excel_file = pd.ExcelFile(str(path), engine=engine)
        sheet_names = list(excel_file.sheet_names)
        if not sheet_names:
            raise ValueError("Workbook has no sheets.")

        if requested_sheet not in (None, "auto"):
            selected_sheet: str | int = requested_sheet
        else:
            selected_sheet = ExcelReader._auto_select_sheet(path, engine, sheet_names)

        if isinstance(selected_sheet, str) and selected_sheet not in sheet_names:
            raise ValueError(
                f"Requested sheet '{selected_sheet}' not found. Available sheets: {sheet_names}"
            )

        if requested_header is None:
            header_row: Optional[int] = None
        elif isinstance(requested_header, int):
            header_row = requested_header
        elif requested_header == "auto":
            preview = pd.read_excel(
                str(path),
                sheet_name=selected_sheet,
                header=None,
                nrows=25,
                engine=engine,
            )
            header_row = ExcelReader._detect_header_row(preview)
        else:
            raise ValueError(
                f"Invalid header argument '{requested_header}'. Use int, None, or 'auto'."
            )

        return SheetSelection(sheet_name=selected_sheet, header_row=header_row)

    @staticmethod
    def _auto_select_sheet(
        path: Path,
        engine: Optional[str],
        sheet_names: List[str],
    ) -> str:
        scored: List[tuple[str, float]] = []
        for sheet in sheet_names:
            preview = pd.read_excel(
                str(path),
                sheet_name=sheet,
                header=None,
                nrows=25,
                engine=engine,
            )
            if preview.empty:
                scored.append((sheet, -1.0))
                continue

            header_idx = ExcelReader._detect_header_row(preview)
            non_empty = float((preview.dropna(how="all").shape[0]))
            data_rows = max(non_empty - (header_idx + 1), 0.0)
            header_score = ExcelReader._header_row_score(preview.iloc[header_idx])
            score = (header_score * 0.7) + (min(data_rows / 25.0, 1.0) * 0.3)
            scored.append((sheet, score))

        scored.sort(key=lambda item: (-item[1], item[0]))
        top_sheet, top_score = scored[0]
        if top_score < 0:
            raise ValueError("No usable sheet detected in workbook.")
        return top_sheet

    @staticmethod
    def _detect_header_row(preview: pd.DataFrame) -> int:
        if preview.empty:
            return 0

        best_row = 0
        best_score = -1.0
        scan_limit = min(len(preview), 25)
        for idx in range(scan_limit):
            score = ExcelReader._header_row_score(preview.iloc[idx])
            if score > best_score:
                best_score = score
                best_row = idx
        return int(best_row)

    @staticmethod
    def _header_row_score(row: pd.Series) -> float:
        non_null = row.dropna()
        if non_null.empty:
            return -1.0
        if len(non_null) == 1:
            return -0.3

        text = non_null.astype(str).str.strip()
        unique_ratio = text.nunique() / float(max(len(text), 1))
        alpha_ratio = float(text.str.contains(r"[A-Za-z]", regex=True).mean())
        numeric_ratio = float(text.str.fullmatch(r"-?\d+(\.\d+)?", na=False).mean())
        punctuation_penalty = float(text.str.fullmatch(r"[-_=]+", na=False).mean())

        return (
            unique_ratio * 0.45
            + alpha_ratio * 0.4
            + (1.0 - numeric_ratio) * 0.15
            - punctuation_penalty * 0.2
        )

    @staticmethod
    def _normalize_columns(columns: Iterable[Any]) -> pd.Index:
        normalized = (
            pd.Index(columns)
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
            .str.replace(r"[^a-z0-9_]+", "", regex=True)
        )
        return normalized

    @staticmethod
    def _validate_temporal_columns(df: pd.DataFrame, sheet_name: str | int) -> None:
        temporal_tokens = ("date", "time", "timestamp")
        for column in df.columns:
            col_name = str(column).lower()
            is_temporal = any(token in col_name for token in temporal_tokens)
            if col_name == "event_time":
                is_temporal = True
            if not is_temporal:
                continue

            series = df[column]
            if pd.api.types.is_datetime64_any_dtype(series):
                continue

            non_null = series.dropna().astype(str).str.strip()
            if len(non_null) < 5:
                continue

            parsed = pd.to_datetime(non_null, errors="coerce", utc=True)
            valid = int(parsed.notna().sum())
            if valid == 0:
                raise ValueError(
                    f"Date parsing failed for column '{column}' in sheet '{sheet_name}'. "
                    "No valid timestamps detected."
                )
            if valid / float(len(non_null)) < 0.4:
                raise ValueError(
                    f"Date parsing unstable for column '{column}' in sheet '{sheet_name}'. "
                    f"Only {valid}/{len(non_null)} values parsed as dates."
                )

    @staticmethod
    def _engine_candidates(suffix: str) -> List[Optional[str]]:
        if suffix in {".xlsx", ".xlsm", ".xltx"}:
            return ["openpyxl", None]
        return [None]
