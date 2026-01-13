from pathlib import Path
from typing import Dict

import pandas as pd
import yaml


class TimeAligner:
    """
    Aligns heterogeneous industrial datasets to a unified event-time-based timeline
    using configuration-driven rules.
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Dict = self._load_config()

    def _load_config(self) -> Dict:
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def normalize_timestamp(
        self,
        df: pd.DataFrame,
        time_column: str
    ) -> pd.DataFrame:
        """
        Convert timestamps to timezone-aware values and normalize
        them to the configured base timezone.
        """
        df = df.copy()

        series = pd.to_datetime(df[time_column], errors="coerce")

        if series.dt.tz is None:
            series = series.dt.tz_localize(
                self.config["time_strategy"]["base_timezone"]
            )
        else:
            series = series.dt.tz_convert(
                self.config["time_strategy"]["base_timezone"]
            )

        df[time_column] = series
        return df

    def align_to_window(
        self,
        df: pd.DataFrame,
        time_column: str,
        window: str
    ) -> pd.DataFrame:
        """
        Align timestamps to a fixed rolling window using a DatetimeIndex
        to ensure static type safety and runtime correctness.
        """
        df = df.copy()

        dt_index = pd.DatetimeIndex(df[time_column])
        df["aligned_time"] = dt_index.floor(window)

        return df

    def apply_alignment(
        self,
        df: pd.DataFrame,
        source: str
    ) -> pd.DataFrame:
        """
        Apply source-specific time alignment rules defined in configuration.
        """
        rules = self.config["alignment_rules"].get(source)

        if rules is None:
            raise ValueError(
                f"No time alignment rules defined for source: {source}"
            )

        time_column = rules["align_on"]
        window = self.config["windows"]["default_window"]

        df = self.normalize_timestamp(df, time_column)
        df = self.align_to_window(df, time_column, window)

        return df