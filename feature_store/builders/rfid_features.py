from typing import Dict
import pandas as pd

from feature_store.builders.base_builder import BaseFeatureBuilder


class RFIDFeatureBuilder(BaseFeatureBuilder):
    """
    Feature builder for RFID-based operator activity data.

    Produces operator-level presence and activity-related features
    from cleaned and time-aligned RFID event logs.
    """

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def entity(self) -> str:
        return "operator"

    def source(self) -> str:
        return "rfid"

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build RFID-derived operator features.

        Expected input columns (minimum):
        - operator_id
        - aligned_time
        - event_type
        """
        required_columns = {
            "operator_id",
            "aligned_time",
            "event_type",
        }

        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(
                f"RFIDFeatureBuilder missing required columns: {missing}"
            )

        data = df.copy()

        # Presence is inferred from any RFID event in the window
        grouped = data.groupby(
            ["operator_id", "aligned_time"],
            as_index=False
        )

        features = grouped.agg(
            presence_event_count=("event_type", "count"),
        )

        # Idle-but-present:
        # operator present but only passive events observed
        active_events = {"MOVE", "WORK", "INTERACT"}

        activity_df = (
            data.assign(
                is_active=data["event_type"].isin(active_events)
            )
            .groupby(["operator_id", "aligned_time"], as_index=False)
            .agg(
                active_event_ratio=("is_active", "mean"),
            )
        )

        result = pd.merge(
            features,
            activity_df,
            on=["operator_id", "aligned_time"],
            how="inner",
        )

        result["idle_but_present"] = result["active_event_ratio"] == 0.0

        return result