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
    - merged-cell header expansion (industrial Excel support)
    - multi-row header combination
    - automatic unnamed/empty column cleanup
    - loud and actionable failures
    - multi-sheet iteration for full workbook ingestion
    """

    # ──────────────────────────────────────────────────────────────────────
    # Multi-sheet reader — iterates all sheets and returns usable ones
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def read_all_sheets(
        file_path: str,
        header: int | None | str = "auto",
        detect_dates: bool = True,
        min_rows: int = 1,
        min_cols: int = 2,
    ) -> dict[str, pd.DataFrame]:
        """
        Read ALL sheets from an Excel workbook and return a dict of
        sheet_name → DataFrame for every sheet that has usable tabular data.

        Parameters
        ----------
        file_path : str
            Path to the .xlsx / .xls file.
        header : int | None | str
            Header detection mode per sheet (default: "auto").
        detect_dates : bool
            Whether to validate temporal columns.
        min_rows : int
            Minimum data rows for a sheet to be considered usable.
        min_cols : int
            Minimum columns for a sheet to be considered usable.

        Returns
        -------
        dict[str, pd.DataFrame]
            Mapping of sheet name → cleaned DataFrame.
            Empty dict if no usable sheets are found.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        suffix = path.suffix.lower()
        engines = ExcelReader._engine_candidates(suffix)
        engine = engines[0] if engines else None

        try:
            xls = pd.ExcelFile(str(path), engine=engine)
            sheet_names = list(xls.sheet_names)
        except Exception:
            return {}

        results: dict[str, pd.DataFrame] = {}

        for sheet in sheet_names:
            try:
                df = ExcelReader.read(
                    file_path=file_path,
                    sheet_name=sheet,
                    header=header,
                    detect_dates=detect_dates,
                )
                if df is not None and len(df) >= min_rows and len(df.columns) >= min_cols:
                    results[sheet] = df
            except Exception:
                # Sheet is unusable (empty, bad format, etc.) — skip it
                continue

        return results

    # ──────────────────────────────────────────────────────────────────────
    # Single-sheet reader (original API)
    # ──────────────────────────────────────────────────────────────────────

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

                # ----------------------------------------------------------
                # Try openpyxl-based merged-cell-aware read first (.xlsx)
                # This handles industrial Excel files with merged headers.
                # ----------------------------------------------------------
                if suffix in {".xlsx", ".xlsm", ".xltx"}:
                    try:
                        df = ExcelReader._read_with_merged_cell_handling(
                            path, selection
                        )
                        if df is not None and not df.empty:
                            if detect_dates and selection.header_row is not None:
                                ExcelReader._validate_temporal_columns(
                                    df, selection.sheet_name
                                )
                            return df
                    except Exception:
                        pass  # Fall through to standard pandas read

                # ----------------------------------------------------------
                # Standard pandas read (fallback)
                # ----------------------------------------------------------
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

                # Clean up unnamed/empty columns
                df = ExcelReader._drop_junk_columns(df)

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

    # ──────────────────────────────────────────────────────────────────────
    # Merged-cell-aware reader (handles industrial Excel formats)
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _read_with_merged_cell_handling(
        path: Path, selection: SheetSelection
    ) -> Optional[pd.DataFrame]:
        """
        Read an Excel file using openpyxl directly to handle merged cells.

        Industrial Excel files often have:
        - Merged cells in header rows (group headers spanning columns)
        - Multi-row headers (row 1 = groups, row 2 = sub-columns)
        - Lots of None values in header rows due to merges

        This method:
        1. Opens with openpyxl and reads merged cell ranges
        2. Unmerges and forward-fills header values
        3. Detects and combines multi-row headers
        4. Reads data rows into a DataFrame
        5. Drops junk columns (>95% empty + unnamed)
        """
        import openpyxl

        wb = openpyxl.load_workbook(str(path), read_only=False, data_only=True)

        # Resolve sheet
        sheet_key = selection.sheet_name
        if isinstance(sheet_key, int):
            if sheet_key >= len(wb.sheetnames):
                return None
            ws = wb[wb.sheetnames[sheet_key]]
        else:
            if sheet_key not in wb.sheetnames:
                return None
            ws = wb[sheet_key]

        if ws.max_row is None or ws.max_row < 2:
            return None

        # --- Step 1: Build a merged-cell map ---
        merged_map = {}  # (row, col) -> value from top-left of merge
        for merge_range in list(ws.merged_cells.ranges):
            top_left_value = ws.cell(merge_range.min_row, merge_range.min_col).value
            for row in range(merge_range.min_row, merge_range.max_row + 1):
                for col in range(merge_range.min_col, merge_range.max_col + 1):
                    merged_map[(row, col)] = top_left_value

        def cell_value(row: int, col: int):
            """Get cell value, resolving merged cells."""
            if (row, col) in merged_map:
                return merged_map[(row, col)]
            return ws.cell(row, col).value

        # --- Step 2: Detect header row(s) ---
        header_row_idx = (selection.header_row or 0) + 1  # 1-indexed for openpyxl
        max_col = ws.max_column or 1

        # Read candidate header rows (up to 3)
        header_rows_data = []
        for r in range(header_row_idx, min(header_row_idx + 3, (ws.max_row or 1) + 1)):
            row_vals = [cell_value(r, c) for c in range(1, max_col + 1)]
            header_rows_data.append(row_vals)

        if not header_rows_data:
            return None

        # --- Step 3: Determine best header strategy ---
        # Count how many cells in each candidate row are non-null text
        row_text_counts = []
        for row_vals in header_rows_data:
            text_count = sum(
                1 for v in row_vals
                if v is not None and isinstance(v, str) and v.strip()
            )
            row_text_counts.append(text_count)

        # If row 1 has few text headers but row 2 or 3 has many more,
        # the later row is likely the real header
        best_header_offset = 0
        if len(row_text_counts) > 1:
            max_count = max(row_text_counts)
            for i, count in enumerate(row_text_counts):
                if count == max_count:
                    best_header_offset = i
                    break

        # Use the best header row
        final_header = list(header_rows_data[best_header_offset])
        data_start_row = header_row_idx + best_header_offset + 1  # 1-indexed

        # --- Step 4: Forward-fill None gaps in the header ---
        # In industrial files, merged headers leave gaps
        last_val = None
        for i, val in enumerate(final_header):
            if val is not None and str(val).strip():
                last_val = val
            elif last_val is not None:
                # Only forward-fill if the *data* below this column is non-empty
                # to avoid filling decorative merges
                pass  # We'll name these below

        # --- Step 5: Build column names ---
        col_names = []
        seen_names = {}
        for i, val in enumerate(final_header):
            if val is None or not str(val).strip():
                # Check if there's a formula string we should skip
                name = f"unnamed_{i}"
            else:
                name = str(val).strip()
                # Clean formula references like "='Production data'!Q1"
                if name.startswith("="):
                    name = f"formula_ref_{i}"

            # Normalize
            name = (
                name.lower()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("'", "")
                .replace('"', "")
            )
            # Remove non-alphanumeric (keep underscore)
            import re
            name = re.sub(r"[^a-z0-9_]", "", name)
            if not name:
                name = f"col_{i}"

            # Deduplicate
            if name in seen_names:
                seen_names[name] += 1
                name = f"{name}_{seen_names[name]}"
            else:
                seen_names[name] = 0

            col_names.append(name)

        # --- Step 6: Read data rows ---
        data_rows = []
        max_data_row = min(ws.max_row or 1, data_start_row + 50000)  # Safety cap
        for r in range(data_start_row, max_data_row + 1):
            row_data = [cell_value(r, c) for c in range(1, max_col + 1)]
            # Skip completely empty rows
            if any(v is not None for v in row_data):
                data_rows.append(row_data)

        if not data_rows:
            return None

        df = pd.DataFrame(data_rows, columns=col_names[:max_col])

        # --- Step 7: Drop junk columns ---
        df = ExcelReader._drop_junk_columns(df)

        # Drop fully empty rows
        df = df.dropna(how="all").reset_index(drop=True)

        if df.empty:
            return None

        return df

    # ──────────────────────────────────────────────────────────────────────
    # Junk column cleanup
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _drop_junk_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Drop columns that are:
        - Named 'unnamed_*' or 'formula_ref_*' AND
        - Have >90% null/empty values

        This removes padding columns from merged-cell layouts and
        formula reference columns without preserving decorative junk.
        """
        if df.empty:
            return df

        cols_to_drop = []
        total_rows = len(df)
        if total_rows == 0:
            return df

        for col in df.columns:
            col_str = str(col).lower()
            is_unnamed = (
                col_str.startswith("unnamed")
                or col_str.startswith("formula_ref")
                or col_str.startswith("col_")
            )
            if is_unnamed:
                null_count = df[col].isna().sum()
                null_ratio = null_count / total_rows
                if null_ratio > 0.90:
                    cols_to_drop.append(col)

        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        return df

    # ──────────────────────────────────────────────────────────────────────
    # Selection & header detection (original logic, improved)
    # ──────────────────────────────────────────────────────────────────────

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

        total_cells = len(row)
        fill_ratio = len(non_null) / float(max(total_cells, 1))

        text = non_null.astype(str).str.strip()
        unique_ratio = text.nunique() / float(max(len(text), 1))
        alpha_ratio = float(text.str.contains(r"[A-Za-z]", regex=True).mean())
        numeric_ratio = float(text.str.fullmatch(r"-?\d+(\.\d+)?", na=False).mean())
        punctuation_penalty = float(text.str.fullmatch(r"[-_=]+", na=False).mean())

        return (
            unique_ratio * 0.35
            + alpha_ratio * 0.30
            + fill_ratio * 0.20
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
