import json
from pathlib import Path
import pandas as pd


class TypeValidator:
    """
    Enforces data types defined in schema JSON.
    Performs safe coercion and fails loudly on unrecoverable errors.
    """

    @staticmethod
    def validate(df: pd.DataFrame, schema_path: Path) -> None:
        """
        Validate and coerce column data types.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame
        schema_path : Path
            Path to schema JSON
        """

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        dtype_map = schema.get("dtypes", {})

        for column, expected_type in dtype_map.items():
            if column not in df.columns:
                continue  # schema validator already enforces presence

            try:
                df[column] = TypeValidator._coerce_column(
                    df[column], expected_type
                )
            except Exception as exc:
                raise ValueError(
                    f"Type validation failed for column '{column}' "
                    f"(expected {expected_type}): {exc}"
                ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_column(series: pd.Series, expected_type: str) -> pd.Series:
        """
        Coerce a pandas Series to the expected type.
        """

        expected_type = expected_type.lower()

        if expected_type == "string":
            return series.astype("string")

        if expected_type == "int":
            return pd.to_numeric(
                series, errors="raise"
            ).astype("Int64")  # nullable int

        if expected_type == "float":
            return pd.to_numeric(
                series, errors="raise"
            ).astype("float")

        if expected_type == "bool":
            return series.astype("boolean")

        if expected_type == "datetime":
            # Delegated but enforced here
            return pd.to_datetime(series, errors="raise")

        raise ValueError(f"Unsupported data type '{expected_type}'")
