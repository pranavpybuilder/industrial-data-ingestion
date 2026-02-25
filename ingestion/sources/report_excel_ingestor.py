from pathlib import Path
from typing import Optional

import pandas as pd

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.excel_reader import ExcelReader


class ReportExcelIngestor(BaseIngestor):
    """
    Ingestor for SAP-derived maintenance analysis Excel files.
    """

    EXPECTED_COLUMNS = [
        "date",
        "equipment_number",
        "machine_name",
        "machine_description",
        "user_state",
        "downtime",
        "malfunction_start_date",
        "malfunction_end_date",
        "malfunction_start_time",
        "malfunction_end_time",
        "created",
        "why1",
        "why2",
        "why3",
        "why4",
        "why5",
    ]

    def __init__(
        self,
        source_path: str,
        schema_path: str,
        output_dir: str = "data/raw/reports",
        run_id: Optional[str] = None,
    ):
        super().__init__(
            source_name="report_excel",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
            run_id=run_id,
            schema_type="sap",
        )

    def read(self) -> pd.DataFrame:
        path = Path(self.source_path)
        if not path.exists():
            raise FileNotFoundError(f"Report Excel file not found: {path}")

        return ExcelReader.read(
            file_path=str(path),
            sheet_name="auto",
            header="auto",
        )

    def ingest(self) -> dict:
        raw_df = self.read()
        self._validate_not_empty(raw_df)
        normalized_df = self._normalize_report(raw_df)
        return self.ingest_dataframe(
            data=normalized_df,
            original_column_snapshot=list(raw_df.columns),
        )

    def _normalize_report(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        df = df.dropna(how="all")

        if "downtime" in df.columns:
            df["downtime"] = pd.to_numeric(df["downtime"], errors="coerce")

        df.reset_index(drop=True, inplace=True)
        return df
