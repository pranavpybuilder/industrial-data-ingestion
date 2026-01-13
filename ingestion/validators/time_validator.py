import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd


class TimeValidator:
    """
    Validates and normalizes time columns for industrial datasets.

    Ensures:
    - Presence of time column
    - Valid datetime parsing
    - UTC normalization
    - No future timestamps
    """

    @staticmethod
    def validate(df: pd.DataFrame, schema_path: Path) -> None:
        """
        Validate and normalize the time column defined in schema.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame
        schema_path : Path
            Path to schema JSON
        """

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        time_column = schema.get("time_column")

        if not time_column:
            raise ValueError(
                "Schema must define a 'time_column' for time validation"
            )

        if time_column not in df.columns:
            raise ValueError(
                f"Time column '{time_column}' not found in dataset"
            )

        TimeValidator._parse_time_column(df, time_column)
        TimeValidator._validate_no_future_time(df, time_column)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_time_column(df: pd.DataFrame, column: str) -> None:
        """
        Parse and normalize time column to timezone-aware datetime (UTC).
        """

        try:
            # Strict parsing; will raise on invalid formats
            df[column] = pd.to_datetime(
                df[column],
                errors="raise",
                utc=True,
            )
        except Exception as exc:
            raise ValueError(
                f"Failed to parse datetime values in column '{column}': {exc}"
            ) from exc

    @staticmethod
    def _validate_no_future_time(df: pd.DataFrame, column: str) -> None:
        """
        Ensure no timestamps exist in the future.
        """

        now_utc = datetime.now(timezone.utc)

        future_mask = df[column] > now_utc

        if future_mask.any():
            count = int(future_mask.sum())
            raise ValueError(
                f"Time validation failed: {count} future timestamps detected "
                f"in column '{column}'"
            )