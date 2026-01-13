from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml


class FeatureNormalizer:
    """
    Applies configuration-driven normalization strategies to feature datasets
    and persists normalization metadata for reproducibility.
    """

    def __init__(self, config_path: str, metadata_dir: str) -> None:
        self.config_path = Path(config_path)
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _min_max_scale(
        self, series: pd.Series
    ) -> pd.Series:
        min_val = series.min()
        max_val = series.max()

        if min_val == max_val:
            return pd.Series(0.0, index=series.index)

        return (series - min_val) / (max_val - min_val)

    def _z_score_scale(
        self, series: pd.Series
    ) -> pd.Series:
        mean_val = series.mean()
        std_val = series.std()

        if std_val == 0 or pd.isna(std_val):
            return pd.Series(0.0, index=series.index)

        return (series - mean_val) / std_val

    def normalize(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Normalize features according to configuration.
        """
        df = df.copy()

        strategies = self.config.get("strategies", {})

        applied_metadata: Dict[str, Dict] = {}

        for strategy, columns in strategies.items():
            for column in columns:
                if column not in df.columns:
                    continue

                if strategy == "min_max":
                    df[column] = self._min_max_scale(df[column])
                    applied_metadata[column] = {
                        "strategy": "min_max",
                        "min": float(df[column].min()),
                        "max": float(df[column].max()),
                    }

                elif strategy == "z_score":
                    df[column] = self._z_score_scale(df[column])
                    applied_metadata[column] = {
                        "strategy": "z_score",
                        "mean": float(df[column].mean()),
                        "std": float(df[column].std()),
                    }

                elif strategy == "none":
                    applied_metadata[column] = {
                        "strategy": "none"
                    }

        self._persist_metadata(applied_metadata)
        return df

    def _persist_metadata(self, metadata: Dict[str, Dict]) -> None:
        """
        Persist normalization metadata for auditability and reproducibility.
        """
        metadata_path = self.metadata_dir / "normalization_metadata.yaml"

        with open(metadata_path, "w") as f:
            yaml.safe_dump(metadata, f)