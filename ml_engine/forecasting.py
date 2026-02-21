# ml_engine/forecasting.py

"""
Forecasting Module — Simple trend extrapolation and threshold projection.
Fully offline, no external API calls.
Uses simple linear/polynomial regression, no deep learning.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional


class Forecaster:
    """
    Generates forecasts and threshold violation predictions
    using statistical extrapolation.
    """

    def __init__(self, horizon: int = 10, logger=None):
        self.horizon = horizon
        self.logger = logger

    def forecast(
        self,
        features_df: pd.DataFrame,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate forecasts for key features and detect potential
        threshold violations in the projected future.
        
        Returns list of forecast findings.
        """
        findings = []
        thresholds = thresholds or {}

        if features_df is None or features_df.empty:
            return findings

        grouped = features_df.groupby("feature_name")

        for feature_name, group in grouped:
            values = group["feature_value"].dropna().values

            if len(values) < 10:
                continue

            # Generate forecast
            forecast = self._extrapolate(feature_name, values)
            if not forecast:
                continue

            # Check threshold violations in forecast
            base_name = feature_name.split("__")[-1] if "__" in feature_name else feature_name
            threshold = thresholds.get(base_name)

            if threshold and forecast["projected_max"] > threshold:
                violation_finding = self._threshold_violation_forecast(
                    feature_name, forecast, threshold, len(values)
                )
                if violation_finding:
                    findings.append(violation_finding)

            # Report significant projected changes
            if forecast["change_pct"] > 20:
                findings.append({
                    "type": "FORECAST",
                    "method": "TREND_EXTRAPOLATION",
                    "feature": feature_name,
                    "current_value": round(float(values[-1]), 4),
                    "projected_value": round(float(forecast["projected_values"][-1]), 4),
                    "projected_max": round(float(forecast["projected_max"]), 4),
                    "change_pct": round(float(forecast["change_pct"]), 1),
                    "direction": forecast["direction"],
                    "horizon": self.horizon,
                    "total_samples": len(values),
                    "severity": "HIGH" if forecast["change_pct"] > 50 else "MEDIUM",
                    "confidence": round(min(0.85, forecast["r_squared"]), 2),
                    "message": (
                        f"Forecast: {feature_name} projected to "
                        f"{'increase' if forecast['direction'] == 'UP' else 'decrease'} "
                        f"by {forecast['change_pct']:.0f}% over next {self.horizon} periods. "
                        f"Current: {values[-1]:.2f}, Projected: {forecast['projected_values'][-1]:.2f}"
                    ),
                    "remediation": (
                        f"Plan for {'rising' if forecast['direction'] == 'UP' else 'falling'} "
                        f"{feature_name}. Review maintenance schedule accordingly."
                    ),
                })

        if self.logger:
            self.logger.info(f"Forecasting: {len(findings)} forecast findings")

        return findings

    def _extrapolate(
        self, feature_name: str, values: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Linear regression extrapolation."""
        try:
            n = len(values)
            x = np.arange(n, dtype=float)

            # Fit linear model
            coeffs = np.polyfit(x, values, deg=1)
            slope, intercept = coeffs

            # R-squared
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            if r_squared < 0.1:
                return None

            # Project future values
            future_x = np.arange(n, n + self.horizon, dtype=float)
            projected = np.polyval(coeffs, future_x)

            current_mean = float(np.mean(values[-5:]))
            projected_mean = float(np.mean(projected))
            change_pct = (
                abs(projected_mean - current_mean) / abs(current_mean) * 100
                if current_mean != 0 else 0
            )

            return {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "projected_values": projected.tolist(),
                "projected_max": float(np.max(projected)),
                "projected_min": float(np.min(projected)),
                "change_pct": change_pct,
                "direction": "UP" if slope > 0 else "DOWN",
            }

        except Exception:
            return None

    def _threshold_violation_forecast(
        self,
        feature_name: str,
        forecast: Dict,
        threshold: float,
        sample_count: int,
    ) -> Dict[str, Any]:
        """Generate a threshold violation forecast finding."""
        projected_max = forecast["projected_max"]
        overshoot_pct = (projected_max - threshold) / threshold * 100

        return {
            "type": "FORECAST",
            "method": "THRESHOLD_PROJECTION",
            "feature": feature_name,
            "threshold": threshold,
            "projected_max": round(projected_max, 4),
            "overshoot_pct": round(overshoot_pct, 1),
            "direction": forecast["direction"],
            "r_squared": round(forecast["r_squared"], 3),
            "horizon": self.horizon,
            "total_samples": sample_count,
            "severity": "CRITICAL" if overshoot_pct > 20 else "HIGH",
            "confidence": round(min(0.9, forecast["r_squared"]), 2),
            "message": (
                f"ALERT: {feature_name} projected to exceed threshold of {threshold} "
                f"within {self.horizon} periods (max projected: {projected_max:.2f}, "
                f"overshoot: {overshoot_pct:.0f}%)"
            ),
            "remediation": (
                f"Immediate attention required. {feature_name} is trending toward "
                f"threshold violation. Schedule preventive maintenance before breach."
            ),
        }
