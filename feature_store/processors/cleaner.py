from typing import Dict, List
import pandas as pd


class DataCleaner:
    """
    DataCleaner is responsible for applying deterministic and safe
    data cleaning operations on ingested industrial datasets.

    The cleaner focuses on data reliability rather than aggressive filtering,
    ensuring that real-world industrial signals are preserved while
    removing technical inconsistencies.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def remove_duplicates(
        df: pd.DataFrame,
        subset: List[str] | None = None
    ) -> pd.DataFrame:
        """
        Remove duplicate rows from the dataset.

        Parameters:
        - subset: Optional list of columns to consider for duplicate detection
        """
        df = df.copy()
        return df.drop_duplicates(subset=subset, keep="first")

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        numeric_fill_value: float = 0.0,
        categorical_fill_value: str = "UNKNOWN"
    ) -> pd.DataFrame:
        """
        Handle missing values in a conservative manner.

        - Numeric columns are filled with a default numeric value
        - Categorical columns are filled with a placeholder category
        """
        df = df.copy()

        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].fillna(numeric_fill_value)
            else:
                df[column] = df[column].fillna(categorical_fill_value)

        return df

    @staticmethod
    def enforce_column_types(
        df: pd.DataFrame,
        schema: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Enforce expected column data types based on a schema mapping.

        Schema example:
        {
            "cycle_time": "float",
            "machine_id": "string"
        }
        """
        df = df.copy()

        for column, dtype in schema.items():
            if column not in df.columns:
                continue

            try:
                if dtype == "float":
                    df[column] = pd.to_numeric(df[column], errors="coerce")
                elif dtype == "int":
                    df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
                elif dtype == "string":
                    df[column] = df[column].astype(str)
                elif dtype == "bool":
                    df[column] = df[column].astype(bool)
            except Exception:
                # Fail-safe: never crash cleaning due to one column
                continue

        return df

    def clean(
        self,
        df: pd.DataFrame,
        schema: Dict[str, str] | None = None,
        duplicate_subset: List[str] | None = None
    ) -> pd.DataFrame:
        """
        Execute the full cleaning pipeline in a deterministic order.
        """
        df = self.remove_duplicates(df, subset=duplicate_subset)
        df = self.handle_missing_values(df)

        if schema is not None:
            df = self.enforce_column_types(df, schema)

        return df
