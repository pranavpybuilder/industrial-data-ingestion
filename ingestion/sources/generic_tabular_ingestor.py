from pathlib import Path
from typing import Optional

import pandas as pd

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.csv_reader import CSVReader
from ingestion.readers.excel_reader import ExcelReader


class GenericTabularIngestor(BaseIngestor):
    """
    Flexible ingestor for unknown CSV/XLSX files.

    Used when a file does not match strict SAP/PLC/RFID/report schemas.
    """

    def __init__(
        self,
        source_path: str,
        output_dir: str,
        run_id: Optional[str] = None,
        schema_type: str = "generic",
    ):
        source_label = "energy" if schema_type == "energy" else "generic_tabular"
        super().__init__(
            source_name=source_label,
            source_path=source_path,
            schema_path=None,
            output_dir=output_dir,
            run_id=run_id,
            schema_type=schema_type,
        )

    def read(self) -> pd.DataFrame:
        path = Path(self.source_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return CSVReader.read(str(path))

        if suffix in [".xlsx", ".xls"]:
            return ExcelReader.read(
                file_path=str(path),
                sheet_name="auto",
                header="auto",
            )

        raise ValueError(
            f"Unsupported generic tabular format '{suffix}'. "
            "Only CSV/XLSX/XLS are allowed."
        )

    def ingest(self) -> dict:
        raw_df = self.read()
        self._validate_not_empty(raw_df)

        normalized_df = self._normalize(raw_df)
        self._validate_not_empty(normalized_df)

        metadata = self.ingest_dataframe(
            data=normalized_df,
            original_column_snapshot=list(raw_df.columns),
        )
        metadata["detected_time_column"] = (
            "event_time" if "event_time" in metadata.get("columns", []) else None
        )
        return metadata

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized.columns = (
            normalized.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
            .str.replace(r"[^a-z0-9_]+", "", regex=True)
        )
        normalized = normalized.dropna(how="all").reset_index(drop=True)

        for column in normalized.columns:
            numeric = pd.to_numeric(normalized[column], errors="coerce")
            if numeric.notna().mean() >= 0.85:
                normalized[column] = numeric

        return normalized
