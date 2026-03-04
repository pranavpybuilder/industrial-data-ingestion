# profiling/column_classifier.py

"""
Column Classifier - Categorizes each column in a dataset.

Responsibilities:
  - Analyze column values and determine type (numeric, categorical, temporal, etc.)
  - Handle edge cases (mixed types, nulls, etc.)
  - Provide confidence scores for classification
  - Return structured classification results

Output Type Categories:
  • numeric       → int/float columns (measurement data)
  • categorical   → string with < N unique values (facility, status, product)
  • temporal      → datetime/timestamp columns
  • identifier    → high cardinality strings (UUID, run_id, order_id)
  • boolean       → binary columns (0/1, True/False, yes/no)
  • text          → free-form text (descriptions, notes)
"""

from typing import Dict, List, Tuple, Any
from pathlib import Path
import warnings

import pandas as pd
import numpy as np
from datetime import datetime as dt

from utils.logger import get_logger

logger = get_logger(__name__)


class ColumnClassifier:
    """
    Classifies DataFrame columns by analyzing their content and structure.
    """

    # Configuration thresholds
    CATEGORICAL_MAX_UNIQUE_PCT = 0.05  # Max 5% unique values → categorical
    IDENTIFIER_MIN_UNIQUE_PCT = 0.95   # Min 95% unique values → identifier
    NUMERIC_COVERAGE_MIN = 0.8         # Min 80% numeric → numeric column

    def __init__(self) -> None:
        """Initialize classifier with sklearn optional import."""
        pass

    def classify(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Classify all columns in a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe to classify

        Returns
        -------
        dict: {
            "column_name": {
                "detected_type": "numeric" | "categorical" | "temporal" | 
                                 "identifier" | "boolean" | "text",
                "confidence": 0.0-1.0,
                "cardinality": int (unique count),
                "null_count": int,
                "sample_values": [list of up to 5 values],
                "notes": "reason for classification"
            }
        }
        """
        results = {}

        for col_name in df.columns:
            col_type = self._classify_column(df[col_name])
            results[col_name] = col_type

        logger.info(f"Classified {len(results)} columns in dataframe")
        return results

    def _classify_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Classify a single column by examining its values.
        """
        col_name = series.name
        non_null = series.dropna()
        total_count = len(series)
        null_count = series.isna().sum()

        # Edge case: all null
        if len(non_null) == 0:
            return {
                "detected_type": "unknown",
                "confidence": 0.0,
                "cardinality": 0,
                "null_count": null_count,
                "sample_values": [],
                "notes": "Column is entirely null"
            }

        # Check each type in order of priority
        # Priority: temporal > boolean > numeric > identifier > categorical > text

        # 1. Temporal detection
        temporal_result = self._check_temporal(non_null)
        if temporal_result["score"] > 0.8:
            return {
                "detected_type": "temporal",
                "confidence": temporal_result["score"],
                "cardinality": len(non_null.unique()),
                "null_count": null_count,
                "sample_values": non_null.unique()[:5].tolist(),
                "notes": temporal_result["reason"]
            }

        # 2. Boolean detection
        boolean_result = self._check_boolean(non_null)
        if boolean_result["score"] > 0.9:
            return {
                "detected_type": "boolean",
                "confidence": boolean_result["score"],
                "cardinality": len(non_null.unique()),
                "null_count": null_count,
                "sample_values": non_null.unique()[:5].tolist(),
                "notes": boolean_result["reason"]
            }

        # 3. Numeric detection
        numeric_result = self._check_numeric(non_null)
        if numeric_result["score"] > 0.8:
            return {
                "detected_type": "numeric",
                "confidence": numeric_result["score"],
                "cardinality": len(non_null.unique()),
                "null_count": null_count,
                "sample_values": non_null.unique()[:5].tolist() if len(non_null.unique()) <= 5 else non_null.sample(min(5, len(non_null))).tolist(),
                "notes": numeric_result["reason"]
            }

        # 4. Identifier detection (high cardinality strings)
        unique_ratio = len(non_null.unique()) / len(non_null)
        if unique_ratio >= self.IDENTIFIER_MIN_UNIQUE_PCT and non_null.dtype == 'object':
            return {
                "detected_type": "identifier",
                "confidence": 0.95,
                "cardinality": len(non_null.unique()),
                "null_count": null_count,
                "sample_values": non_null.unique()[:5].tolist(),
                "notes": f"High cardinality ({unique_ratio:.1%} unique) suggests identifier or UUID"
            }

        # 5. Categorical detection (low cardinality strings)
        if non_null.dtype == 'object':
            unique_count = len(non_null.unique())
            unique_ratio = unique_count / len(non_null)

            if unique_count <= 50 and unique_ratio <= 0.3:
                return {
                    "detected_type": "categorical",
                    "confidence": 0.9,
                    "cardinality": unique_count,
                    "null_count": null_count,
                    "sample_values": non_null.unique()[:5].tolist(),
                    "notes": f"Low cardinality ({unique_count} unique values) suggests category"
                }

        # 6. Default: Text
        return {
            "detected_type": "text",
            "confidence": 0.5,
            "cardinality": len(non_null.unique()),
            "null_count": null_count,
            "sample_values": non_null.unique()[:5].tolist(),
            "notes": "String column with high variance - treated as free-form text"
        }

    def _check_numeric(self, series: pd.Series) -> Dict[str, Any]:
        """Check if series is numeric (int or float)."""
        # Already numeric dtype
        if pd.api.types.is_numeric_dtype(series):
            return {
                "score": 0.95,
                "reason": f"Native numeric type ({series.dtype})"
            }

        # Try to convert to numeric
        try:
            pd.to_numeric(series)
            return {
                "score": 0.85,
                "reason": "All values convertible to numeric"
            }
        except (ValueError, TypeError):
            pass

        # Count how many are numeric-like
        try:
            numeric_count = 0
            for val in series:
                try:
                    float(val)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass

            coverage = numeric_count / len(series)
            if coverage >= self.NUMERIC_COVERAGE_MIN:
                return {
                    "score": coverage * 0.9,
                    "reason": f"{coverage:.1%} of values convertible to numeric"
                }
        except Exception:
            pass

        return {"score": 0.0, "reason": "Not numeric"}

    def _check_boolean(self, series: pd.Series) -> Dict[str, Any]:
        """Check if series is boolean (0/1, True/False, yes/no, etc.)."""
        unique_vals = set(series.dropna().unique())

        # Common boolean representations
        boolean_sets = [
            {0, 1},
            {True, False},
            {"true", "false"},
            {"True", "False"},
            {"yes", "no"},
            {"Yes", "No"},
            {"Y", "N"},
            {"y", "n"},
            {1.0, 0.0},
        ]

        # Normalize to strings for comparison
        try:
            normalized = {str(v).lower() for v in unique_vals}
            for bool_set in boolean_sets:
                normalized_bool = {str(v).lower() for v in bool_set}
                if normalized == normalized_bool:
                    return {
                        "score": 0.95,
                        "reason": f"Matches boolean pattern: {bool_set}"
                    }
        except Exception:
            pass

        # If only 2 unique values, might be boolean
        if len(unique_vals) == 2:
            return {
                "score": 0.6,
                "reason": "Only 2 unique values (might be boolean)"
            }

        return {"score": 0.0, "reason": "Not boolean"}

    def _check_temporal(self, series: pd.Series) -> Dict[str, Any]:
        """Check if series is temporal (datetime/timestamp)."""
        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return {
                "score": 0.99,
                "reason": "Native datetime type"
            }

        # Try to parse as datetime
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                pd.to_datetime(series, errors='coerce')
                # Check how many parsed successfully
                parsed = pd.to_datetime(series, errors='coerce')
            success_rate = 1 - parsed.isna().sum() / len(series)

            if success_rate >= 0.8:
                return {
                    "score": success_rate * 0.95,
                    "reason": f"{success_rate:.1%} of values parse as datetime"
                }
        except Exception:
            pass

        # Check for common datetime patterns in strings
        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',     # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',     # MM/DD/YYYY
            r'\d{4}/\d{2}/\d{2}',     # YYYY/MM/DD
            r'\d{2}-\d{2}-\d{4}',     # DD-MM-YYYY
        ]

        if series.dtype == 'object':
            import re
            pattern_matches = 0
            for val in series.dropna().iloc[:min(100, len(series))]:  # Sample first 100
                val_str = str(val)
                for pattern in datetime_patterns:
                    if re.match(pattern, val_str):
                        pattern_matches += 1
                        break

            if len(series) > 0 and pattern_matches / len(series) > 0.8:
                return {
                    "score": 0.85,
                    "reason": "String values match datetime patterns"
                }

        return {"score": 0.0, "reason": "Not temporal"}


# Test helper function
def get_classifier() -> ColumnClassifier:
    """Factory function to get classifier instance."""
    return ColumnClassifier()
