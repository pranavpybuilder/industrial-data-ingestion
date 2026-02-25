from pathlib import Path
import pandas as pd
from typing import Optional

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.csv_reader import CSVReader
from ingestion.readers.json_reader import JSONReader


class RFIDIngestor(BaseIngestor):
    """
    Ingestor for industrial RFID event data.

    Handles:
    - CSV and JSON RFID logs
    - Duplicate read suppression
    - Basic event normalization
    """

    def __init__(
        self,
        source_path: str,
        schema_path: str,
        output_dir: str = "data/raw/rfid",
        run_id: Optional[str] = None,
    ):
        super().__init__(
            source_name="rfid",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
            run_id=run_id,
            schema_type="rfid",
        )

    # ------------------------------------------------------------------
    # Mandatory implementation
    # ------------------------------------------------------------------

    def read(self) -> pd.DataFrame:
        """
        Read RFID data from CSV or JSON file.
        """

        path = Path(self.source_path)

        if not path.exists():
            raise FileNotFoundError(f"RFID file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = CSVReader.read(str(path))     # Path → str
        elif suffix == ".json":
            df = JSONReader.read(str(path))    # Path → str
        else:
            raise ValueError(
                "Unsupported RFID file format. "
                "Expected CSV or JSON."
            )

        return df

    # ------------------------------------------------------------------
    # Override optional normalization hook
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        """
        Extend base ingestion with RFID-specific normalization.
        """
        raw_df = self.read()
        self._validate_not_empty(raw_df)
        normalized_df = self._normalize_events(raw_df)
        return self.ingest_dataframe(
            data=normalized_df,
            original_column_snapshot=list(raw_df.columns),
        )

    # ------------------------------------------------------------------
    # RFID-specific logic
    # ------------------------------------------------------------------

    def _normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize RFID event data:
        - Remove duplicate reads
        """

        # Drop exact duplicate reads
        dedupe_cols = [
            col
            for col in ["tag_id", "reader_id", "event_time"]
            if col in df.columns
        ]

        if dedupe_cols:
            df = df.drop_duplicates(subset=dedupe_cols)

        df = df.reset_index(drop=True)

        return df
