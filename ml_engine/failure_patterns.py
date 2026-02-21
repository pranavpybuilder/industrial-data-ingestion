# ml_engine/failure_patterns.py

"""
Failure Pattern Detection — Identifies recurring patterns, trends, and degradation.
Fully offline, no external API calls.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional


class FailurePatternDetector:
    """
    Detects failure patterns in time-series feature data:
    - Uptrends (degradation over time)
    - Spikes (sudden changes)
    - Cyclic patterns (recurring failures)
    """

    def __init__(self, logger=None):
        self.logger = logger

    def detect(self, features_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect failure patterns in long-format feature data.
        
        Returns list of pattern findings.
        """
        findings = []

        if features_df is None or features_df.empty:
            return findings

        grouped = features_df.groupby("feature_name")

        for feature_name, group in grouped:
            values = group["feature_value"].dropna().values

            if len(values) < 5:
                continue

            # ── Trend detection ──
            trend = self._detect_trend(feature_name, values)
            if trend:
                findings.append(trend)

            # ── Spike detection ──
            spike = self._detect_spikes(feature_name, values)
            if spike:
                findings.append(spike)

            # ── Variance change detection ──
            variance = self._detect_variance_shift(feature_name, values)
            if variance:
                findings.append(variance)

        if self.logger:
            self.logger.info(f"Pattern detection: {len(findings)} patterns found")

        return findings

    def _detect_trend(
        self, feature_name: str, values: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Detect significant upward or downward trends using linear regression."""
        try:
            x = np.arange(len(values), dtype=float)
            # Simple linear regression slope
            n = len(values)
            x_mean = np.mean(x)
            y_mean = np.mean(values)
            numerator = np.sum((x - x_mean) * (values - y_mean))
            denominator = np.sum((x - x_mean) ** 2)

            if denominator == 0:
                return None

            slope = numerator / denominator
            y_range = np.max(values) - np.min(values)

            if y_range == 0:
                return None

            # Normalized slope (relative to data range)
            normalized_slope = abs(slope * n) / y_range

            if normalized_slope < 0.3:
                return None

            direction = "UPTREND" if slope > 0 else "DOWNTREND"
            severity = "HIGH" if normalized_slope > 0.6 else "MEDIUM"

            return {
                "type": "PATTERN",
                "method": "TREND_DETECTION",
                "pattern_type": direction,
                "feature": feature_name,
                "slope": round(float(slope), 6),
                "normalized_slope": round(float(normalized_slope), 3),
                "total_samples": len(values),
                "severity": severity,
                "confidence": round(min(0.95, 0.6 + normalized_slope * 0.3), 2),
                "message": (
                    f"{direction} detected for '{feature_name}': "
                    f"slope={slope:.4f} over {len(values)} samples. "
                    f"Range: {np.min(values):.2f} → {np.max(values):.2f}"
                ),
                "remediation": (
                    f"{'Monitor for degradation' if slope > 0 else 'Investigate declining values'} "
                    f"in {feature_name}. Schedule preventive maintenance inspection."
                ),
            }

        except Exception:
            return None

    def _detect_spikes(
        self, feature_name: str, values: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Detect sudden spikes using rolling window comparison."""
        if len(values) < 10:
            return None

        try:
            window_size = max(3, len(values) // 10)
            rolling_mean = pd.Series(values).rolling(window=window_size, min_periods=1).mean().values
            rolling_std = pd.Series(values).rolling(window=window_size, min_periods=1).std().values
            rolling_std = np.where(rolling_std == 0, 1e-10, rolling_std)

            deviations = np.abs(values - rolling_mean) / rolling_std
            spike_count = int(np.sum(deviations > 3.0))

            if spike_count == 0:
                return None

            spike_pct = spike_count / len(values) * 100
            max_deviation = float(np.max(deviations))

            return {
                "type": "PATTERN",
                "method": "SPIKE_DETECTION",
                "pattern_type": "SUDDEN_SPIKE",
                "feature": feature_name,
                "spike_count": spike_count,
                "spike_pct": round(spike_pct, 1),
                "max_deviation": round(max_deviation, 2),
                "total_samples": len(values),
                "severity": "CRITICAL" if spike_pct > 15 else "HIGH" if spike_pct > 5 else "MEDIUM",
                "confidence": round(min(0.9, 0.65 + spike_pct / 50), 2),
                "message": (
                    f"Sudden spikes detected in '{feature_name}': "
                    f"{spike_count} spikes ({spike_pct:.1f}%) with "
                    f"max deviation of {max_deviation:.1f}σ"
                ),
                "remediation": (
                    f"Investigate sudden changes in {feature_name}. "
                    f"May indicate equipment malfunction or sensor issues."
                ),
            }

        except Exception:
            return None

    def _detect_variance_shift(
        self, feature_name: str, values: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Detect significant shifts in variance between first and second half."""
        if len(values) < 20:
            return None

        try:
            mid = len(values) // 2
            var_first = np.var(values[:mid])
            var_second = np.var(values[mid:])

            if var_first == 0 and var_second == 0:
                return None

            # F-ratio for variance comparison
            if var_first == 0:
                ratio = float("inf")
            else:
                ratio = var_second / var_first

            if ratio < 2.0 and ratio > 0.5:
                return None

            direction = "INCREASING" if ratio > 1 else "DECREASING"
            severity = "HIGH" if ratio > 3.0 or ratio < 0.33 else "MEDIUM"

            return {
                "type": "PATTERN",
                "method": "VARIANCE_SHIFT",
                "pattern_type": f"VARIANCE_{direction}",
                "feature": feature_name,
                "variance_ratio": round(float(ratio), 3),
                "first_half_var": round(float(var_first), 4),
                "second_half_var": round(float(var_second), 4),
                "total_samples": len(values),
                "severity": severity,
                "confidence": round(min(0.85, 0.5 + abs(ratio - 1) * 0.15), 2),
                "message": (
                    f"Variance shift in '{feature_name}': "
                    f"{direction.lower()} instability (ratio={ratio:.2f}). "
                    f"First half std={np.sqrt(var_first):.3f}, "
                    f"Second half std={np.sqrt(var_second):.3f}"
                ),
                "remediation": (
                    f"Equipment producing {feature_name} shows {'increasing' if ratio > 1 else 'decreasing'} "
                    f"instability. Schedule inspection."
                ),
            }

        except Exception:
            return None
