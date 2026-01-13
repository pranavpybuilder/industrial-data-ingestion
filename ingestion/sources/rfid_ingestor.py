from pathlib import Path
import pandas as pd

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
    ):
        super().__init__(
            source_name="rfid",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
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

        df = self.read()
        self._validate_not_empty(df)

        # RFID-specific cleanup BEFORE schema enforcement
        df = self._normalize_events(df)

        # Standard pipeline
        self._validate_schema(df)
        self._validate_types(df)
        self._validate_time(df)

        versioned_path = self._persist(df)
        return self._build_metadata(versioned_path, df)

    # ------------------------------------------------------------------
    # RFID-specific logic
    # ------------------------------------------------------------------

    def _normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize RFID event data:
        - Remove duplicate reads
        """

        required_cols = {"tag_id", "event_time", "reader_id"}
        missing = required_cols - set(df.columns)

        if missing:
            raise ValueError(
                f"RFID normalization failed. Missing columns: {missing}"
            )

        # Drop exact duplicate reads
        df = df.drop_duplicates(
            subset=["tag_id", "reader_id", "event_time"]
        ).reset_index(drop=True)

        return df