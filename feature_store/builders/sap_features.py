from typing import Dict
import pandas as pd

from feature_store.builders.base_builder import BaseFeatureBuilder


class SAPFeatureBuilder(BaseFeatureBuilder):
    """
    Feature builder for SAP-derived order and production data.

    Produces order-level features such as planned quantity, actual quantity,
    production variance, and execution duration from cleaned and time-aligned
    SAP exports.
    """

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def entity(self) -> str:
        return "order"

    def source(self) -> str:
        return "sap"

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build SAP-derived order features.

        Expected input columns (minimum):
        - order_id
        - planned_quantity
        - actual_quantity
        - order_start_time
        - order_end_time
        """
        required_columns = {
            "order_id",
            "planned_quantity",
            "actual_quantity",
            "order_start_time",
            "order_end_time",
        }

        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(
                f"SAPFeatureBuilder missing required columns: {missing}"
            )

        data = df.copy()

        # Ensure datetime types
        data["order_start_time"] = pd.to_datetime(
            data["order_start_time"], errors="coerce"
        )
        data["order_end_time"] = pd.to_datetime(
            data["order_end_time"], errors="coerce"
        )

        # Aggregate at order level to handle duplicate SAP rows
        grouped = data.groupby("order_id", as_index=False)

        features = grouped.agg(
            planned_quantity=("planned_quantity", "max"),
            actual_quantity=("actual_quantity", "max"),
            order_start_time=("order_start_time", "min"),
            order_end_time=("order_end_time", "max"),
        )

        # Derived features
        features["production_variance"] = (
            features["actual_quantity"] - features["planned_quantity"]
        )

        # Duration calculation (Pylance-safe)
        duration_index = pd.TimedeltaIndex(
            features["order_end_time"] - features["order_start_time"]
        )

        features["order_duration_minutes"] = (
            duration_index.total_seconds() / 60.0
        )

        return features
