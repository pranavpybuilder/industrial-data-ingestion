from typing import Dict
import pandas as pd

from feature_store.builders.base_builder import BaseFeatureBuilder


class PLCFeatureBuilder(BaseFeatureBuilder):
    """
    Feature builder for PLC / OPC-UA machine data.

    Produces machine-level operational features such as cycle time,
    utilization, and downtime indicators from cleaned and time-aligned
    PLC signals.
    """

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def entity(self) -> str:
        return "machine"

    def source(self) -> str:
        return "plc"

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build PLC-derived machine features.

        Expected input columns (minimum):
        - machine_id
        - aligned_time
        - cycle_time
        - machine_state
        """
        required_columns = {
            "machine_id",
            "aligned_time",
            "cycle_time",
            "machine_state",
        }

        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(
                f"PLCFeatureBuilder missing required columns: {missing}"
            )

        # Work on a copy to avoid side effects
        data = df.copy()

        # --- Aggregations ---
        grouped = data.groupby(
            ["machine_id", "aligned_time"],
            as_index=False
        )

        features = grouped.agg(
            avg_cycle_time_5min=("cycle_time", "mean"),
            sample_count=("cycle_time", "count"),
        )

        # --- Derived Features ---
        # Utilization: proportion of productive states
        productive_states = {"RUNNING", "ON"}

        state_df = (
            data.assign(
                is_productive=data["machine_state"].isin(productive_states)
            )
            .groupby(["machine_id", "aligned_time"], as_index=False)
            .agg(
                machine_utilization=("is_productive", "mean"),
                downtime_flag=("is_productive", lambda x: not x.any()),
            )
        )

        # --- Merge Aggregates ---
        result = pd.merge(
            features,
            state_df,
            on=["machine_id", "aligned_time"],
            how="inner",
        )

        return result