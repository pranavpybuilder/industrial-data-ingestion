from pathlib import Path
import pandas as pd

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.excel_reader import ExcelReader


class ReportExcelIngestor(BaseIngestor):
    """
    Ingestor for SAP-derived maintenance analysis Excel files.

    These files are:
    - Derived from SAP
    - Structured
    - Intended for management dashboards
    - Contain downtime and 5-Why analysis
    """

    # Required columns that MUST be present
    REQUIRED_COLUMNS = [
        "date",
        "equipment_number",
        "machine_name",
        "downtime",
    ]

    # Full set of expected columns (optional ones logged as warnings)
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
    ):
        super().__init__(
            source_name="sap_maintenance_report",
            source_path=source_path,
            schema_path=schema_path,
            output_dir=output_dir,
        )

    # ------------------------------------------------------------------
    # Mandatory implementation
    # ------------------------------------------------------------------

    def read(self) -> pd.DataFrame:
        """
        Read SAP-derived maintenance report Excel.
        """

        path = Path(self.source_path)

        if not path.exists():
            raise FileNotFoundError(f"Report Excel file not found: {path}")

        df = ExcelReader.read(
            file_path=str(path),   # Path → str (Pylance-safe)
            header=0               # headers are expected
        )

        return df

    # ------------------------------------------------------------------
    # Override ingestion for report-specific normalization
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        """
        Ingest SAP-derived maintenance report.
        """

        df = self.read()
        self._validate_not_empty(df)

        df = self._normalize_report(df)

        # Standard pipeline
        self._validate_schema(df)
        self._validate_types(df)
        self._validate_time(df)

        versioned_path = self._persist(df)
        return self._build_metadata(versioned_path, df)

    # ------------------------------------------------------------------
    # Report-specific logic
    # ------------------------------------------------------------------

    def _normalize_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize SAP-derived maintenance report data.
        """

        # Normalize column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # Hard-check: required columns must exist
        missing_required = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_required:
            raise ValueError(
                f"Report Excel missing required columns: {missing_required}"
            )

        # Soft-check: warn about optional columns
        missing_optional = set(self.EXPECTED_COLUMNS) - set(df.columns)
        if missing_optional:
            import logging
            logging.getLogger(__name__).warning(
                f"Report Excel missing optional columns (ignored): {missing_optional}"
            )

        # Remove fully empty rows
        df = df.dropna(how="all")

        # Ensure downtime is numeric
        if "downtime" in df.columns:
            df["downtime"] = pd.to_numeric(
                df["downtime"], errors="coerce"
            )

        df.reset_index(drop=True, inplace=True)
        return df