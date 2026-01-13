from typing import Dict, Tuple
import pandas as pd


class FeatureRangeValidator:
    """
    Validates numerical feature values against predefined acceptable ranges
    to prevent invalid or unsafe data from propagating downstream.
    """

    def __init__(self, ranges: Dict[str, Tuple[float, float]]) -> None:
        """
        Parameters:
        ranges: Dictionary mapping feature names to (min, max) acceptable values.
                Example:
                {
                    "machine_utilization": (0.0, 1.0),
                    "avg_cycle_time_5min": (0.0, 300.0)
                }
        """
        self.ranges = ranges

    def validate(self, df: pd.DataFrame) -> None:
        """
        Validate feature ranges.

        Raises:
            ValueError if any feature violates its defined range.
        """
        for feature, (min_val, max_val) in self.ranges.items():
            if feature not in df.columns:
                continue

            series = df[feature]

            if not pd.api.types.is_numeric_dtype(series):
                continue

            below_min = series < min_val
            above_max = series > max_val

            if below_min.any() or above_max.any():
                invalid_count = int(below_min.sum() + above_max.sum())
                raise ValueError(
                    f"Range validation failed for feature '{feature}'. "
                    f"{invalid_count} value(s) outside range "
                    f"[{min_val}, {max_val}]."
                )
