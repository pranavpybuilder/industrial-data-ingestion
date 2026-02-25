from pathlib import Path
import pandas as pd
from typing import Optional

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.csv_reader import CSVReader
from ingestion.readers.json_reader import JSONReader
from ingestion.readers.log_reader import LogReader


class PLCIngestor(BaseIngestor):
    """
    Ingestor for PLC / OPC-UA machine telemetry and alarm data.

    Supports:
    - CSV exports
    - JSON exports
    - Plain text log files
    """

    def __init__(
        self,
        source_path: str,
        schema_path: str,
        output_dir: str = "data/raw/plc",
        run_id: Optional[str] = None,
    ):
        super().__init__(
            source_name="plc",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
            run_id=run_id,
            schema_type="plc",
        )

    # ------------------------------------------------------------------
    # Mandatory implementation
    # ------------------------------------------------------------------

    def read(self) -> pd.DataFrame:
        """
        Read PLC data from CSV, JSON, or LOG file.
        """

        path = Path(self.source_path)

        if not path.exists():
            raise FileNotFoundError(f"PLC file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = CSVReader.read(str(path))        # Path → str
        elif suffix == ".json":
            df = JSONReader.read(str(path))       # Path → str
        elif suffix in [".log", ".txt"]:
            df = LogReader.read(str(path))        # Path → str
        else:
            raise ValueError(
                "Unsupported PLC file format. "
                "Expected CSV, JSON, or LOG."
            )

        return df

    # ------------------------------------------------------------------
    # Override ingestion for PLC-specific normalization
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        """
        Extend base ingestion with PLC-specific normalization.
        """
        raw_df = self.read()
        self._validate_not_empty(raw_df)
        normalized_df = self._normalize_plc_data(raw_df)
        return self.ingest_dataframe(
            data=normalized_df,
            original_column_snapshot=list(raw_df.columns),
        )

    # ------------------------------------------------------------------
    # PLC-specific logic
    # ------------------------------------------------------------------

    def _normalize_plc_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize PLC telemetry and alarm data.
        """

        # Normalize column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
        )

        # Drop completely empty rows
        df = df.dropna(how="all")

        # Deduplicate repeated PLC events (best-effort)
        dedup_cols = [
            col for col in
            ["machine_id", "event_time", "parameter_name"]
            if col in df.columns
        ]

        if dedup_cols:
            df = df.drop_duplicates(subset=dedup_cols)

        df.reset_index(drop=True, inplace=True)
        return df
