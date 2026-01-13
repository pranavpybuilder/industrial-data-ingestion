import json
from pathlib import Path
import pandas as pd


class SchemaValidator:
    """
    Validates dataset schema against a JSON contract.
    Also handles cases where column headers are not present
    in the first row (common in industrial Excel/CSV files).
    """

    HEADER_SCAN_ROWS = 10  # how many rows to scan for headers

    @staticmethod
    def validate(df: pd.DataFrame, schema_path: Path) -> None:
        """
        Validate DataFrame schema.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame produced by reader
        schema_path : Path
            Path to schema JSON file
        """

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        required_columns = [
            col.strip().lower() for col in schema.get("required_columns", [])
        ]

        # Step 1: Ensure headers exist
        df = SchemaValidator._ensure_headers(df, required_columns)

        # Step 2: Validate required columns
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(
                f"Schema validation failed. Missing columns: {sorted(missing)}"
            )

    # ------------------------------------------------------------------
    # Header handling
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_headers(
        df: pd.DataFrame,
        required_columns: list[str],
    ) -> pd.DataFrame:
        """
        Ensure DataFrame has correct headers.
        Attempts to detect header rows if missing or shifted.
        """

        # Case 1: Columns already look valid
        if SchemaValidator._headers_match(df.columns, required_columns):
            return df

        # Case 2: Try detecting header row inside data
        for row_idx in range(min(len(df), SchemaValidator.HEADER_SCAN_ROWS)):
            potential_headers = (
                df.iloc[row_idx]
                .astype(str)
                .str.strip()
                .str.lower()
                .tolist()
            )

            if SchemaValidator._headers_match(
                potential_headers, required_columns
            ):
                # Rebuild DataFrame using detected header row
                new_df = df.iloc[row_idx + 1 :].copy()
                new_df.columns = potential_headers
                new_df.reset_index(drop=True, inplace=True)
                return new_df

        # Case 3: No headers detected
        raise ValueError(
            "Schema validation failed. "
            "Column headers not found in file or do not match schema."
        )

    @staticmethod
    def _headers_match(headers, required_columns) -> bool:
        """
        Check whether required columns exist in headers.
        """
        normalized_headers = [
            str(col).strip().lower() for col in headers
        ]
        return set(required_columns).issubset(set(normalized_headers))