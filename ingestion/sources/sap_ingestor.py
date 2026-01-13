from pathlib import Path
import pandas as pd

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.csv_reader import CSVReader
from ingestion.readers.excel_reader import ExcelReader


class SAPIngestor(BaseIngestor):
    """
    Ingestor for SAP PM (IW29-style) maintenance order exports.

    Supports:
    - CSV exports
    - Excel exports
    """

    def __init__(
        self,
        source_path: str,
        schema_path: str,
        output_dir: str = "data/raw/sap",
    ):
        super().__init__(
            source_name="sap_iw29",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
        )

    # ------------------------------------------------------------------
    # Mandatory implementation
    # ------------------------------------------------------------------

    def read(self) -> pd.DataFrame:
        """
        Read SAP IW29 data from CSV or Excel export.
        """

        path = Path(self.source_path)

        if not path.exists():
            raise FileNotFoundError(f"SAP file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = CSVReader.read(str(path))        # Path → str
        elif suffix in [".xlsx", ".xls"]:
            df = ExcelReader.read(str(path))      # Path → str
        else:
            raise ValueError(
                "Unsupported SAP file format. "
                "Expected CSV or Excel."
            )

        return df

    # ------------------------------------------------------------------
    # Override ingestion for SAP-specific normalization
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        """
        Extend base ingestion with SAP-specific normalization.
        """

        df = self.read()
        self._validate_not_empty(df)

        df = self._normalize_sap_columns(df)

        # Standard pipeline
        self._validate_schema(df)
        self._validate_types(df)
        self._validate_time(df)

        versioned_path = self._persist(df)
        return self._build_metadata(versioned_path, df)

    # ------------------------------------------------------------------
    # SAP-specific logic
    # ------------------------------------------------------------------

    def _normalize_sap_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize SAP IW29 column names and basic cleanup.
        """

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
        )

        # Drop completely empty rows (common in SAP exports)
        df = df.dropna(how="all")

        df.reset_index(drop=True, inplace=True)
        return df