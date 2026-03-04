# profiling/data_profiler.py

"""
Data Profiler - Computes statistical profiles for each column.

Responsibilities:
  - Calculate descriptive statistics (mean, median, std, min, max, quartiles)
  - Detect outliers using IQR method
  - Compute distribution characteristics
  - Generate quality metrics (completeness, consistency)
  - Return structured profile per column

Output: Detailed column statistics for data quality assessment
"""

from typing import Dict, List, Any, Optional
import warnings
import numpy as np
import pandas as pd
from scipy import stats

from utils.logger import get_logger
from profiling.column_classifier import ColumnClassifier

logger = get_logger(__name__)


class ColumnProfile:
    """Container for a single column's statistical profile."""

    def __init__(self, column_name: str, col_type: str, confidence: float, series: pd.Series):
        self.column_name = column_name
        self.col_type = col_type
        self.confidence = confidence
        self.series = series
        self.non_null = series.dropna()

    def compute(self) -> Dict[str, Any]:
        """
        Compute all statistics for this column based on its type.
        """
        profile = {
            "column_name": self.column_name,
            "detected_type": self.col_type,
            "confidence": self.confidence,
            "total_count": len(self.series),
            "null_count": self.series.isna().sum(),
            "null_percentage": (self.series.isna().sum() / len(self.series)) * 100,
            "unique_count": len(self.series.unique()),
        }

        # Type-specific statistics
        if self.col_type == "numeric":
            profile.update(self._profile_numeric())

        elif self.col_type == "categorical":
            profile.update(self._profile_categorical())

        elif self.col_type == "temporal":
            profile.update(self._profile_temporal())

        elif self.col_type == "boolean":
            profile.update(self._profile_boolean())

        else:  # identifier, text, unknown
            profile.update(self._profile_string())

        return profile

    @staticmethod
    def _safe_float(val, default: float = 0.0) -> float:
        """Safely convert to float, handling pd.NA / NAType / None."""
        if val is None:
            return default
        try:
            result = float(val)
            if result != result:           # NaN check
                return default
            return result
        except (TypeError, ValueError):
            return default

    def _profile_numeric(self) -> Dict[str, Any]:
        """Profile numeric columns."""
        if len(self.non_null) == 0:
            return {}

        numeric_values = pd.to_numeric(self.non_null, errors='coerce').dropna()

        if len(numeric_values) == 0:
            return {}

        sf = self._safe_float
        mean_val = sf(numeric_values.mean())
        median_val = sf(numeric_values.median())
        std_val = sf(numeric_values.std())
        min_val = sf(numeric_values.min())
        max_val = sf(numeric_values.max())

        # Quartiles
        q1 = sf(numeric_values.quantile(0.25))
        q3 = sf(numeric_values.quantile(0.75))
        iqr = q3 - q1

        # Outliers (IQR method)
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = numeric_values[(numeric_values < lower_bound) | (numeric_values > upper_bound)]
        outlier_count = len(outliers)
        outlier_percentage = (outlier_count / len(numeric_values)) * 100

        # Distribution characteristics
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                skewness = float(stats.skew(numeric_values))
                kurtosis = float(stats.kurtosis(numeric_values))
        except Exception:
            skewness = 0.0
            kurtosis = 0.0

        return {
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "std": round(std_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "outlier_count": int(outlier_count),
            "outlier_percentage": round(outlier_percentage, 2),
            "skewness": round(skewness, 4),
            "kurtosis": round(kurtosis, 4),
            "range": round(max_val - min_val, 4),
            "cv": round(std_val / mean_val, 4) if mean_val != 0 else 0.0,  # coefficient of variation
        }

    def _profile_categorical(self) -> Dict[str, Any]:
        """Profile categorical columns."""
        if len(self.non_null) == 0:
            return {}

        value_counts = self.non_null.value_counts()
        top_values = value_counts.head(10).to_dict()
        mode_value = self.non_null.mode()[0] if len(self.non_null.mode()) > 0 else None
        mode_freq = value_counts.iloc[0] if len(value_counts) > 0 else 0

        # Diversity (Shannon entropy)
        probabilities = value_counts / len(self.non_null)
        entropy = -sum(probabilities * np.log2(probabilities + 1e-10))
        max_entropy = np.log2(len(value_counts)) if len(value_counts) > 0 else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return {
            "unique_values": int(len(value_counts)),
            "mode": str(mode_value),
            "mode_frequency": int(mode_freq),
            "uniqueness_ratio": round(len(value_counts) / len(self.non_null), 4),
            "top_values": {str(k): int(v) for k, v in list(top_values.items())[:5]},
            "diversity_entropy": round(entropy, 4),
            "normalized_entropy": round(normalized_entropy, 4),
        }

    def _profile_temporal(self) -> Dict[str, Any]:
        """Profile temporal columns."""
        if len(self.non_null) == 0:
            return {}

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                dates = pd.to_datetime(self.non_null, errors='coerce').dropna()

            if len(dates) == 0:
                return {}

            min_date = dates.min()
            max_date = dates.max()
            date_range = (max_date - min_date).days

            # Frequency of observations
            time_diff = dates.diff().dropna().dt.total_seconds() / 86400  # Convert to days
            mean_interval = float(time_diff.mean()) if len(time_diff) > 0 else None
            median_interval = float(time_diff.median()) if len(time_diff) > 0 else None

            return {
                "min_date": str(min_date),
                "max_date": str(max_date),
                "date_range_days": int(date_range),
                "mean_interval_days": round(mean_interval, 2) if mean_interval else None,
                "median_interval_days": round(median_interval, 2) if median_interval else None,
                "timezone_aware": bool(dates.dt.tz),
                "frequency": self._infer_frequency(dates),
            }
        except Exception as e:
            logger.warning(f"Error profiling temporal column {self.column_name}: {e}")
            return {}

    def _profile_boolean(self) -> Dict[str, Any]:
        """Profile boolean columns."""
        if len(self.non_null) == 0:
            return {}

        value_counts = self.non_null.value_counts()
        true_count = (value_counts.get(True, 0) or value_counts.get(1, 0)
                      or value_counts.get('True', 0) or value_counts.get('true', 0) or 0)
        if hasattr(true_count, 'iloc'):
            true_count = true_count.iloc[0] if len(true_count) > 0 else 0
        false_count = len(self.non_null) - true_count
        true_percentage = (true_count / len(self.non_null)) * 100

        return {
            "true_count": int(true_count),
            "false_count": int(false_count),
            "true_percentage": round(true_percentage, 2),
            "false_percentage": round(100 - true_percentage, 2),
            "balance": "balanced" if 40 <= true_percentage <= 60 else "imbalanced",
        }

    def _profile_string(self) -> Dict[str, Any]:
        """Profile string/text columns."""
        if len(self.non_null) == 0:
            return {}

        if not isinstance(self.non_null.iloc[0], str):
            return {}

        lengths = self.non_null.str.len()

        return {
            "avg_length": round(float(lengths.mean()), 2),
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "median_length": round(float(lengths.median()), 2),
            "unique_values": int(len(self.non_null.unique())),
            "uniqueness_ratio": round(len(self.non_null.unique()) / len(self.non_null), 4),
        }

    def _infer_frequency(self, dates: pd.Series) -> Optional[str]:
        """Infer observation frequency (daily, hourly, etc.)."""
        if len(dates) < 2:
            return None

        time_diffs = dates.diff().dropna()
        if len(time_diffs) == 0:
            return None

        median_diff = time_diffs.median()
        total_seconds = median_diff.total_seconds()

        if total_seconds < 3600:  # < 1 hour
            return "sub-hourly"
        elif total_seconds < 86400:  # < 1 day
            return "hourly"
        elif total_seconds < 86400 * 7:  # < 1 week
            return "daily"
        elif total_seconds < 86400 * 30:  # < 1 month
            return "weekly"
        else:
            return "monthly"


class DataProfiler:
    """
    Main profiler that orchestrates column classification and statistical profiling.
    """

    def __init__(self):
        self.classifier = ColumnClassifier()

    def profile(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Profile all columns in a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe to profile

        Returns
        -------
        dict: {
            "column_name": {
                "column_name": str,
                "detected_type": str,
                "confidence": float,
                "null_count": int,
                "null_percentage": float,
                "unique_count": int,
                ... (type-specific statistics)
            }
        }
        """
        # Step 1: Classify columns
        classifications = self.classifier.classify(df)
        logger.info(f"Classified {len(classifications)} columns")

        # Step 2: Profile each column
        profiles = {}
        for col_name, classification in classifications.items():
            column_profile = ColumnProfile(
                column_name=col_name,
                col_type=classification["detected_type"],
                confidence=classification["confidence"],
                series=df[col_name],
            )
            profiles[col_name] = column_profile.compute()

        logger.info(f"Profiled {len(profiles)} columns successfully")
        return profiles

    def profile_to_db_format(self, df: pd.DataFrame, run_id: str) -> List[Dict[str, Any]]:
        """
        Profile DataFrame and convert to database insertion format.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        run_id : str
            Associated run ID for database

        Returns
        -------
        list: [{
            "run_id": str,
            "column_name": str,
            "missing_percentage": float,
            "outlier_count": int,
            "detected_type": str,
            "health_status": str (good/warning/alert)
        }]
        """
        profiles = self.profile(df)

        db_records = []
        for col_name, profile in profiles.items():
            null_pct = profile.get("null_percentage", 0)
            outlier_count = profile.get("outlier_count", 0)

            # Determine health status
            if null_pct > 30 or outlier_count > len(df) * 0.1:
                health_status = "alert"
            elif null_pct > 10 or outlier_count > len(df) * 0.05:
                health_status = "warning"
            else:
                health_status = "good"

            db_records.append({
                "run_id": run_id,
                "column_name": col_name,
                "missing_percentage": round(null_pct, 2),
                "outlier_count": outlier_count,
                "detected_type": profile.get("detected_type", "unknown"),
                "health_status": health_status,
            })

        return db_records


# Test helper function
def get_profiler() -> DataProfiler:
    """Factory function to get profiler instance."""
    return DataProfiler()
