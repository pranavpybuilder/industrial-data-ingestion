# profiling/data_health.py

"""
Data Health - Computes overall data quality health score.

Responsibilities:
  - Calculate 5 health dimensions:
    1. Completeness (% non-null)
    2. Consistency (type conformance, value validity)
    3. Uniqueness (for identifier columns)
    4. Validity (range checks, format validation)
    5. Freshness (recency of data for temporal columns)
  - Combine into single health score (0-100)
  - Flag specific issues per column
  - Return actionable health report

Output: Overall 0-100 health score + column-level issues
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np

from utils.logger import get_logger
from profiling.data_profiler import DataProfiler

logger = get_logger(__name__)


class HealthReport:
    """Container for data health assessment results."""

    def __init__(self, run_id: str, df: pd.DataFrame):
        self.run_id = run_id
        self.df = df
        self.profiler = DataProfiler()
        self.profiles = {}
        self.dimensions = {}
        self.overall_score = 0.0
        self.issues = []

    def compute(self) -> Dict[str, Any]:
        """
        Compute complete health assessment.

        Returns
        -------
        dict: {
            "run_id": str,
            "overall_health_score": 0-100,
            "health_status": "critical" | "poor" | "fair" | "good" | "excellent",
            "total_rows": int,
            "total_columns": int,
            "dimensions": {
                "completeness": 0-100,
                "consistency": 0-100,
                "uniqueness": 0-100,
                "validity": 0-100,
                "freshness": 0-100,
            },
            "column_issues": [
                {"column_name": str, "severity": str, "message": str}
            ],
            "summary": str
        }
        """
        logger.info(f"Computing health assessment for run {self.run_id}")

        # Get profiles
        self.profiles = self.profiler.profile(self.df)

        # Compute each dimension
        self.dimensions["completeness"] = self._assess_completeness()
        self.dimensions["consistency"] = self._assess_consistency()
        self.dimensions["uniqueness"] = self._assess_uniqueness()
        self.dimensions["validity"] = self._assess_validity()
        self.dimensions["freshness"] = self._assess_freshness()

        # Overall score is weighted average
        weights = {
            "completeness": 0.25,
            "consistency": 0.25,
            "uniqueness": 0.15,
            "validity": 0.20,
            "freshness": 0.15,
        }

        self.overall_score = sum(
            self.dimensions[dim] * weights[dim]
            for dim in self.dimensions
        )

        # Determine health status label
        if self.overall_score >= 90:
            health_status = "excellent"
        elif self.overall_score >= 75:
            health_status = "good"
        elif self.overall_score >= 60:
            health_status = "fair"
        elif self.overall_score >= 40:
            health_status = "poor"
        else:
            health_status = "critical"

        # Identify specific issues
        self._identify_issues()

        # Generate summary
        summary = self._generate_summary()

        return {
            "run_id": self.run_id,
            "overall_health_score": round(self.overall_score, 2),
            "health_status": health_status,
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "column_issues": self.issues,
            "summary": summary,
        }

    def _assess_completeness(self) -> float:
        """
        Assess completeness: % of non-null values.
        
        Score:
        - 100%: No nulls
        - 90-100%: <10% nulls (good)
        - 70-90%: 10-30% nulls (fair)
        - 50-70%: 30-50% nulls (poor)
        - <50%: >50% nulls (critical)
        """
        null_pct = self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns)) * 100
        total_missing_pct = self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns)) * 100

        if total_missing_pct == 0:
            return 100.0
        elif total_missing_pct <= 10:
            return 90.0 + (10 - total_missing_pct)
        elif total_missing_pct <= 30:
            return 70.0 + (30 - total_missing_pct) * (20 / 20)
        elif total_missing_pct <= 50:
            return 50.0 + (50 - total_missing_pct) * (20 / 20)
        else:
            return max(0.0, 50.0 - (total_missing_pct - 50))

    def _assess_consistency(self) -> float:
        """
        Assess consistency: type conformance, no unexpected nulls in key columns.
        
        Checks:
        - All values in numeric columns are actually numeric
        - All values in boolean columns are 0/1/True/False
        - No sudden type changes
        """
        issues_detected = 0
        total_checks = 0

        for col_name, profile in self.profiles.items():
            detected_type = profile.get("detected_type", "unknown")
            null_pct = profile.get("null_percentage", 0)

            if detected_type == "numeric":
                total_checks += 1
                # Try to convert all non-null values to numeric
                try:
                    numeric_vals = pd.to_numeric(self.df[col_name].dropna(), errors='coerce')
                    if numeric_vals.isna().sum() > 0:
                        issues_detected += 1
                except Exception:
                    issues_detected += 1

            elif detected_type == "boolean":
                total_checks += 1
                valid_bool_vals = {0, 1, True, False, 'true', 'false', 'True', 'False', 'yes', 'no', 'Yes', 'No'}
                invalid = self.df[col_name].dropna().apply(lambda x: x not in valid_bool_vals)
                if invalid.any():
                    issues_detected += 1

        if total_checks == 0:
            return 95.0  # Safe score if no numeric/boolean columns

        consistency_pct = (1 - issues_detected / total_checks) * 100
        return max(50.0, consistency_pct)

    def _assess_uniqueness(self) -> float:
        """
        Assess uniqueness: identifier columns should have no duplicates.
        
        Score:
        - 100: All identifiers unique
        - 80-100: <5% duplicates
        - 60-80: 5-15% duplicates
        - <60: >15% duplicates
        """
        uniqueness_scores = []

        for col_name, profile in self.profiles.items():
            if profile.get("detected_type") == "identifier":
                unique_count = profile.get("unique_count", 0)
                total_count = profile.get("total_count", 1)
                duplicates_pct = (1 - unique_count / total_count) * 100

                if duplicates_pct == 0:
                    uniqueness_scores.append(100.0)
                elif duplicates_pct <= 5:
                    uniqueness_scores.append(95.0)
                elif duplicates_pct <= 15:
                    uniqueness_scores.append(70.0)
                else:
                    uniqueness_scores.append(max(40.0, 100 - duplicates_pct * 2))

        # If no identifier columns, default to good
        return sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 85.0

    def _assess_validity(self) -> float:
        """
        Assess validity: values within expected ranges.
        
        Checks:
        - Numeric: no extreme outliers
        - Dates: within reasonable range
        - Categories: expected categories present
        """
        validity_scores = []

        for col_name, profile in self.profiles.items():
            detected_type = profile.get("detected_type", "unknown")

            if detected_type == "numeric":
                outlier_pct = profile.get("outlier_percentage", 0)
                if outlier_pct <= 1:
                    validity_scores.append(100.0)
                elif outlier_pct <= 5:
                    validity_scores.append(95.0)
                elif outlier_pct <= 10:
                    validity_scores.append(85.0)
                else:
                    validity_scores.append(max(50.0, 100 - outlier_pct * 3))

            elif detected_type == "temporal":
                date_range = profile.get("date_range_days", 0)
                if date_range > 0:
                    validity_scores.append(90.0)  # Assuming reasonable date range
                else:
                    validity_scores.append(70.0)

        return sum(validity_scores) / len(validity_scores) if validity_scores else 80.0

    def _assess_freshness(self) -> float:
        """
        Assess freshness: how recent is the data?
        
        Looks for temporal columns and checks how recent data is.
        """
        from datetime import datetime, timedelta

        freshness_scores = []

        for col_name, profile in self.profiles.items():
            if profile.get("detected_type") == "temporal":
                try:
                    max_date_str = profile.get("max_date")
                    if max_date_str:
                        max_date = pd.to_datetime(max_date_str)
                        now = pd.Timestamp.now()
                        days_old = (now - max_date).days

                        if days_old <= 1:
                            freshness_scores.append(100.0)
                        elif days_old <= 7:
                            freshness_scores.append(95.0)
                        elif days_old <= 30:
                            freshness_scores.append(80.0)
                        elif days_old <= 90:
                            freshness_scores.append(60.0)
                        else:
                            freshness_scores.append(max(30.0, 100 - days_old / 10))
                except Exception:
                    freshness_scores.append(70.0)

        # If no temporal columns, assume data is fresh
        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else 85.0

    def _identify_issues(self) -> None:
        """Identify specific data quality issues."""
        self.issues = []

        for col_name, profile in self.profiles.items():
            null_pct = profile.get("null_percentage", 0)
            detected_type = profile.get("detected_type", "unknown")
            outlier_pct = profile.get("outlier_percentage", 0)

            # Missing data
            if null_pct > 30:
                self.issues.append({
                    "column_name": col_name,
                    "severity": "critical",
                    "message": f"Column is {null_pct:.1f}% null - consider removing or imputing"
                })
            elif null_pct > 10:
                self.issues.append({
                    "column_name": col_name,
                    "severity": "warning",
                    "message": f"Column has {null_pct:.1f}% missing values"
                })

            # Outliers
            if detected_type == "numeric" and outlier_pct > 10:
                self.issues.append({
                    "column_name": col_name,
                    "severity": "warning",
                    "message": f"Column has {outlier_pct:.1f}% outliers - check for data entry errors"
                })

            # Low cardinality concerning for identifiers
            if detected_type == "identifier":
                unique_ratio = profile.get("uniqueness_ratio", 0)
                if unique_ratio < 0.9:
                    self.issues.append({
                        "column_name": col_name,
                        "severity": "warning",
                        "message": f"Identifier column has only {unique_ratio:.1%} uniqueness - duplicates detected"
                    })

    def _generate_summary(self) -> str:
        """Generate a human-readable health summary."""
        completeness = self.dimensions["completeness"]
        consistency = self.dimensions["consistency"]
        validity = self.dimensions["validity"]

        if self.overall_score >= 90:
            base = "Dataset is in excellent condition. "
        elif self.overall_score >= 75:
            base = "Dataset is in good condition. "
        elif self.overall_score >= 60:
            base = "Dataset is acceptable but has some quality issues. "
        else:
            base = "Dataset has significant quality concerns. "

        issues_count = len(self.issues)
        critical_issues = sum(1 for i in self.issues if i["severity"] == "critical")

        if critical_issues > 0:
            base += f"{critical_issues} critical issue(s) require immediate attention. "

        if issues_count > 0:
            base += f"See {issues_count} total issue(s) identified below."
        else:
            base += "No specific issues detected."

        return base


def compute_data_health(run_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convenience function to compute data health for a dataframe.

    Parameters
    ----------
    run_id : str
        Associated run ID
    df : pd.DataFrame
        Input dataframe

    Returns
    -------
    dict: Health report with overall score and detailed assessments
    """
    report = HealthReport(run_id, df)
    return report.compute()
