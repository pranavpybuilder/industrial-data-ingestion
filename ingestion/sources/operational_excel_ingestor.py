import pandas as pd
from typing import Optional

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.excel_reader import ExcelReader


class OperationalExcelIngestor(BaseIngestor):
    """
    Ingestor for messy, human-maintained operational Excel files.

    Characteristics:
    - No fixed schema
    - Headers may appear anywhere
    - Multiple tables possible
    - Notes and metadata mixed with data

    Philosophy:
    Ingest first, understand later.
    """

    def __init__(
        self,
        source_path: str,
        output_dir: str = "data/raw/operational_excels",
        run_id: Optional[str] = None,
    ):
        super().__init__(
            source_name="operational_excel",
            source_path=source_path,
            schema_path="",   # schema-less by design (empty string for typing safety)
            output_dir=output_dir,
            run_id=run_id,
            schema_type="generic",
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        raw_df = self._read_raw_sheet()
        self._validate_not_empty(raw_df)

        prepared = self._prepare_primary_table(raw_df)
        self._validate_not_empty(prepared)

        metadata = self.ingest_dataframe(
            data=prepared,
            original_column_snapshot=[str(c) for c in raw_df.columns],
        )
        metadata["tables_detected"] = 1
        metadata["notes"] = []

        return metadata

    # ------------------------------------------------------------------
    # Step 1: Read entire sheet with zero assumptions
    # ------------------------------------------------------------------

    def _read_raw_sheet(self) -> pd.DataFrame:
        return ExcelReader.read(
            file_path=str(self.source_path),
            sheet_name="auto",
            header=None
        )

    # ------------------------------------------------------------------
    # Step 2: Row profiling (heuristics)
    # ------------------------------------------------------------------

    def _prepare_primary_table(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a usable tabular DataFrame from a schema-less Excel sheet.
        """
        header_idx = self._detect_header_row(raw_df)

        if header_idx is None:
            df = raw_df.copy()
            df.columns = [f"col_{i+1}" for i in range(df.shape[1])]
        else:
            headers = (
                raw_df.iloc[header_idx]
                .fillna("")
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
            )
            df = raw_df.iloc[header_idx + 1 :].copy()
            df.columns = headers.fillna(
                pd.Series(
                    [f"col_{i+1}" for i in range(len(headers))],
                    index=headers.index,
                )
            )

        df = df.dropna(how="all").reset_index(drop=True)
        df.columns = (
            pd.Index(df.columns)
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
            .str.replace(r"[^a-z0-9_]+", "", regex=True)
        )

        # Coerce mostly-numeric columns to numeric
        for column in df.columns:
            numeric = pd.to_numeric(df[column], errors="coerce")
            if numeric.notna().mean() >= 0.8:
                df[column] = numeric

        return df

    def _detect_header_row(self, df: pd.DataFrame) -> Optional[int]:
        scan_limit = min(len(df), 15)
        best_idx: Optional[int] = None
        best_score = 0.0

        for row_idx in range(scan_limit):
            row = df.iloc[row_idx]
            non_null = row.dropna()
            if non_null.empty:
                continue

            as_text = non_null.astype(str).str.strip()
            unique_ratio = as_text.nunique() / max(len(as_text), 1)
            alpha_ratio = as_text.str.contains(r"[A-Za-z]", regex=True).mean()
            score = unique_ratio * 0.6 + alpha_ratio * 0.4

            if score > best_score and len(non_null) >= 2:
                best_idx = row_idx
                best_score = score

        return best_idx
