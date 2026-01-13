from typing import Dict, List
import pandas as pd


class FeatureSchemaValidator:
    """
    Validates feature DataFrames against expected schema definitions
    to ensure downstream analytics and ML safety.
    """

    def __init__(self, schema: Dict[str, str]) -> None:
        """
        Parameters:
        schema: Dictionary mapping column names to expected data types.
                Example:
                {
                    "machine_id": "string",
                    "avg_cycle_time_5min": "float"
                }
        """
        self.schema = schema

    def validate_columns(
        self, df: pd.DataFrame
    ) -> None:
        """
        Ensure all required columns exist in the DataFrame.
        """
        missing_columns: List[str] = [
            col for col in self.schema.keys()
            if col not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Feature schema validation failed. "
                f"Missing columns: {missing_columns}"
            )

    def validate_types(
        self, df: pd.DataFrame
    ) -> None:
        """
        Validate column data types at a high level.
        """
        for column, expected_type in self.schema.items():
            series = df[column]

            if expected_type == "float":
                if not pd.api.types.is_numeric_dtype(series):
                    raise TypeError(
                        f"Column '{column}' is expected to be numeric."
                    )

            elif expected_type == "int":
                if not pd.api.types.is_integer_dtype(series):
                    raise TypeError(
                        f"Column '{column}' is expected to be integer."
                    )

            elif expected_type == "string":
                if not pd.api.types.is_object_dtype(series):
                    raise TypeError(
                        f"Column '{column}' is expected to be string."
                    )

            elif expected_type == "bool":
                if not pd.api.types.is_bool_dtype(series):
                    raise TypeError(
                        f"Column '{column}' is expected to be boolean."
                    )

    def validate(
        self, df: pd.DataFrame
    ) -> None:
        """
        Run full schema validation.
        """
        self.validate_columns(df)
        self.validate_types(df)