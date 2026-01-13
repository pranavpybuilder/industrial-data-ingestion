from typing import Dict, List
import pandas as pd

from feature_store.builders.base_builder import BaseFeatureBuilder


class ExcelFeatureBuilder(BaseFeatureBuilder):
    """
    Feature builder for Excel-based maintenance and operational reports.

    Handles SAP-derived KPI Excel files and human-maintained operational
    Excel sheets by extracting stable numeric indicators and manual flags
    without enforcing rigid schema assumptions.
    """

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def entity(self) -> str:
        return "machine"

    def source(self) -> str:
        return "excel"

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build Excel-derived features.

        Expected input columns (minimum):
        - machine_id
        - aligned_time

        Optional columns:
        - oee
        - downtime_minutes
        - scrap_rate
        - manual_flag
        """
        required_columns = {
            "machine_id",
            "aligned_time",
        }

        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(
                f"ExcelFeatureBuilder missing required columns: {missing}"
            )

        data = df.copy()

        feature_columns: List[str] = []

        # Optional KPI-style numeric features
        numeric_candidates = [
            "oee",
            "downtime_minutes",
            "scrap_rate",
        ]

        for col in numeric_candidates:
            if col in data.columns:
                feature_columns.append(col)

        # Optional manual flags / indicators
        if "manual_flag" in data.columns:
            data["manual_flag"] = data["manual_flag"].astype(bool)
            feature_columns.append("manual_flag")

        # If no optional features exist, return minimal presence indicator
        if not feature_columns:
            result = data[["machine_id", "aligned_time"]].copy()
            result["excel_record_present"] = True
            return result

        # Aggregate Excel features per machine and time window
        grouped = data.groupby(
            ["machine_id", "aligned_time"],
            as_index=False
        )

        aggregation_rules = {
            col: "mean" for col in feature_columns
            if col != "manual_flag"
        }

        if "manual_flag" in feature_columns:
            aggregation_rules["manual_flag"] = "any"

        result = grouped.agg(aggregation_rules)

        return result