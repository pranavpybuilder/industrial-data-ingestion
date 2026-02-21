# ml_engine/anomaly_detection.py

"""
Anomaly Detection Module — Isolation Forest + statistical methods.
Fully offline, no external API calls.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """
    Detects anomalies in numeric features using Isolation Forest
    and statistical methods (Z-score, IQR).
    """

    def __init__(self, contamination: float = 0.1, logger=None):
        self.contamination = contamination
        self.logger = logger

    def detect(
        self,
        features_df: pd.DataFrame,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run anomaly detection on long-format feature data.
        
        Parameters
        ----------
        features_df : pd.DataFrame
            Long-format: [run_id, feature_name, feature_value, feature_type, timestamp]
        thresholds : dict, optional
            Feature-specific thresholds for rule-based anomaly tagging.
        
        Returns
        -------
        list of anomaly findings
        """
        findings = []
        thresholds = thresholds or {}

        if features_df is None or features_df.empty:
            return findings

        # Group by feature name
        grouped = features_df.groupby("feature_name")

        for feature_name, group in grouped:
            values = group["feature_value"].dropna().values

            if len(values) < 5:
                continue

            # ── Statistical anomaly detection ──
            stat_anomalies = self._statistical_anomalies(feature_name, values)
            if stat_anomalies:
                findings.append(stat_anomalies)

            # ── Threshold anomaly detection ──
            base_name = feature_name.split("__")[-1] if "__" in feature_name else feature_name
            if base_name in thresholds:
                threshold_finding = self._threshold_anomalies(
                    feature_name, values, thresholds[base_name]
                )
                if threshold_finding:
                    findings.append(threshold_finding)

        # ── Isolation Forest (multivariate) ──
        iso_findings = self._isolation_forest(features_df)
        findings.extend(iso_findings)

        if self.logger:
            self.logger.info(f"Anomaly detection: {len(findings)} anomalies found")

        return findings

    def _statistical_anomalies(
        self, feature_name: str, values: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Z-score based anomaly detection."""
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return None

        z_scores = np.abs((values - mean) / std)
        anomaly_count = int(np.sum(z_scores > 3.0))

        if anomaly_count == 0:
            return None

        anomaly_pct = anomaly_count / len(values) * 100

        return {
            "type": "ANOMALY",
            "method": "Z_SCORE",
            "feature": feature_name,
            "anomaly_count": anomaly_count,
            "anomaly_pct": round(anomaly_pct, 1),
            "total_samples": len(values),
            "mean": round(float(mean), 4),
            "std": round(float(std), 4),
            "severity": "CRITICAL" if anomaly_pct > 10 else "HIGH" if anomaly_pct > 5 else "MEDIUM",
            "confidence": round(min(0.95, 0.7 + anomaly_pct / 100), 2),
            "message": (
                f"Statistical anomaly: {anomaly_count} values ({anomaly_pct:.1f}%) "
                f"exceed 3σ threshold for '{feature_name}'. "
                f"Mean={mean:.2f}, Std={std:.2f}"
            ),
            "remediation": (
                f"Investigate {feature_name} readings outside normal range. "
                f"Check sensor calibration and equipment condition."
            ),
        }

    def _threshold_anomalies(
        self, feature_name: str, values: np.ndarray, threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Threshold-based anomaly detection."""
        violations = int(np.sum(values > threshold))
        if violations == 0:
            return None

        violation_pct = violations / len(values) * 100
        max_val = float(np.max(values))

        return {
            "type": "ANOMALY",
            "method": "THRESHOLD",
            "feature": feature_name,
            "anomaly_count": violations,
            "anomaly_pct": round(violation_pct, 1),
            "threshold": threshold,
            "max_value": round(max_val, 4),
            "severity": "CRITICAL" if max_val > threshold * 1.5 else "HIGH",
            "confidence": 0.95,
            "message": (
                f"Threshold violation: {violations} readings ({violation_pct:.1f}%) "
                f"exceed limit of {threshold} for '{feature_name}'. Max={max_val:.2f}"
            ),
            "remediation": (
                f"Immediate inspection required for equipment related to {feature_name}. "
                f"Values exceed operational safety threshold."
            ),
        }

    def _isolation_forest(
        self, features_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Multivariate anomaly detection using Isolation Forest."""
        findings = []

        try:
            # Pivot to wide format for multivariate analysis
            pivot = features_df.pivot_table(
                index=features_df.index,
                columns="feature_name",
                values="feature_value",
                aggfunc="first",
            )

            if pivot.shape[0] < 10 or pivot.shape[1] < 2:
                return findings

            # Drop columns with >50% missing
            pivot = pivot.dropna(axis=1, thresh=int(pivot.shape[0] * 0.5))
            pivot = pivot.fillna(pivot.median())

            if pivot.shape[1] < 2:
                return findings

            # Scale features
            scaler = StandardScaler()
            X = scaler.fit_transform(pivot.values)

            # Fit Isolation Forest
            iso = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
            )
            predictions = iso.fit_predict(X)
            scores = iso.decision_function(X)

            anomaly_count = int(np.sum(predictions == -1))
            if anomaly_count > 0:
                findings.append({
                    "type": "ANOMALY",
                    "method": "ISOLATION_FOREST",
                    "feature": "MULTIVARIATE",
                    "anomaly_count": anomaly_count,
                    "anomaly_pct": round(anomaly_count / len(predictions) * 100, 1),
                    "total_samples": len(predictions),
                    "features_analyzed": list(pivot.columns),
                    "severity": "HIGH" if anomaly_count > len(predictions) * 0.15 else "MEDIUM",
                    "confidence": round(0.85 - 0.1 * (anomaly_count / len(predictions)), 2),
                    "message": (
                        f"Isolation Forest detected {anomaly_count} multivariate anomalies "
                        f"across {pivot.shape[1]} features ({len(predictions)} samples)."
                    ),
                    "remediation": (
                        "Review flagged time periods for equipment health. "
                        "Cross-reference with maintenance logs for root cause."
                    ),
                })

        except Exception as exc:
            if self.logger:
                self.logger.warning(f"Isolation Forest failed (non-fatal): {exc}")

        return findings
