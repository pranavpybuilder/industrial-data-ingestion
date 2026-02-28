"""
Anomaly Detection — Multi-method ensemble for industrial data.

Methods:
1. Isolation Forest (sklearn) — main unsupervised anomaly detector
2. Z-Score — statistical outlier detection (>3σ from mean)
3. IQR Fence — interquartile range outlier detection

Ensemble scoring:
- Each method produces a 0-1 anomaly score per row
- Final score = weighted average: IF(0.5) + Z(0.25) + IQR(0.25)
- Findings only produced for rows where ensemble score > 0.5

Tested against: Breakdown_data.csv (57 rows × 7 numeric columns)
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_engine.model_evaluator import ModelEvaluator


class AnomalyDetector:
    """
    Multi-method anomaly detector combining Isolation Forest, Z-Score, and IQR.

    Each method produces a normalized 0-1 score. The ensemble combines them
    with configurable weights to produce a final anomaly score.
    """

    def __init__(
        self,
        random_state: int = 42,
        if_weight: float = 0.50,
        zscore_weight: float = 0.25,
        iqr_weight: float = 0.25,
    ) -> None:
        self.random_state = random_state
        self.if_weight = if_weight
        self.zscore_weight = zscore_weight
        self.iqr_weight = iqr_weight
        self.model: Optional[IsolationForest] = None

    def detect(self, feature_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Run all anomaly detection methods and produce ensemble findings.

        Parameters
        ----------
        feature_matrix : pd.DataFrame
            Numeric feature matrix (rows = observations, columns = features).
            Must have at least 12 rows.

        Returns
        -------
        list of dict
            Each dict contains: type, feature_name, severity, confidence,
            anomaly_score, detection_method, description, current_value, timestamp
        """
        if feature_matrix.empty or len(feature_matrix) < 12:
            return []

        matrix = feature_matrix.select_dtypes(include=["number"]).copy()
        if matrix.empty:
            return []

        matrix = matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # ── Method 1: Isolation Forest ──
        if_scores = self._isolation_forest_scores(matrix)

        # ── Method 2: Z-Score ──
        zscore_scores = self._zscore_scores(matrix)

        # ── Method 3: IQR Fence ──
        iqr_scores = self._iqr_scores(matrix)

        # ── Ensemble ──
        ensemble_scores = (
            if_scores * self.if_weight
            + zscore_scores * self.zscore_weight
            + iqr_scores * self.iqr_weight
        )

        # ── Generate findings ──
        findings: List[Dict[str, Any]] = []
        for idx in range(len(matrix)):
            score = float(ensemble_scores[idx])
            if score < 0.5:
                continue

            row_values = matrix.iloc[idx].abs()
            top_feature = str(row_values.idxmax())
            top_value = float(matrix.iloc[idx][top_feature])

            severity = "CRITICAL" if score >= 0.8 else "WARNING"
            confidence = ModelEvaluator.confidence_from_anomaly_score(
                score, len(matrix)
            )
            ts = feature_matrix.index[idx]

            # Determine which methods flagged this row
            methods_triggered: List[str] = []
            if if_scores[idx] > 0.5:
                methods_triggered.append("IsolationForest")
            if zscore_scores[idx] > 0.5:
                methods_triggered.append("Z-Score")
            if iqr_scores[idx] > 0.5:
                methods_triggered.append("IQR")

            detection_method = "+".join(methods_triggered) if methods_triggered else "Ensemble"

            findings.append(
                {
                    "type": "ANOMALY",
                    "feature_name": top_feature,
                    "severity": severity,
                    "confidence": confidence,
                    "anomaly_score": score,
                    "detection_method": detection_method,
                    "description": (
                        f"Anomalous behavior detected for '{top_feature}' "
                        f"(value={top_value:.3f}, ensemble_score={score:.3f}). "
                        f"Methods: {detection_method}."
                    ),
                    "current_value": top_value,
                    "timestamp": str(ts),
                    "if_score": float(if_scores[idx]),
                    "zscore_score": float(zscore_scores[idx]),
                    "iqr_score": float(iqr_scores[idx]),
                }
            )

        return findings

    def _isolation_forest_scores(self, matrix: pd.DataFrame) -> np.ndarray:
        """
        Run Isolation Forest and return normalized 0-1 anomaly scores.
        Higher = more anomalous.
        """
        model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=self.random_state,
        )
        model.fit(matrix)
        self.model = model

        raw_scores = -model.score_samples(matrix)  # higher = more anomalous
        return self._normalize_scores(raw_scores)

    def _zscore_scores(self, matrix: pd.DataFrame) -> np.ndarray:
        """
        Compute per-row Z-score anomaly scores.
        For each row, the max absolute Z-score across all columns is used.
        Scores are then normalized to 0-1.
        """
        means = matrix.mean()
        stds = matrix.std()
        # Avoid division by zero
        stds = stds.replace(0, 1.0)

        z_matrix = ((matrix - means) / stds).abs()
        # Per-row max Z-score
        max_z = z_matrix.max(axis=1).to_numpy()

        # Map Z-scores to 0-1 range:
        # Z < 2 → ~0, Z = 3 → 0.5, Z > 4 → ~1
        scores = np.clip((max_z - 2.0) / 2.0, 0.0, 1.0)
        return scores

    def _iqr_scores(self, matrix: pd.DataFrame) -> np.ndarray:
        """
        Compute per-row IQR-based anomaly scores.
        For each column, values beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR are outliers.
        Score = fraction of columns where the row is an outlier.
        """
        q1 = matrix.quantile(0.25)
        q3 = matrix.quantile(0.75)
        iqr = q3 - q1
        # Avoid zero IQR
        iqr = iqr.replace(0, 1e-6)

        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        # Boolean matrix: True if value is an outlier
        outlier_mask = (matrix < lower_fence) | (matrix > upper_fence)

        # Per-row: fraction of columns that are outliers
        scores = outlier_mask.sum(axis=1).to_numpy() / max(matrix.shape[1], 1)
        return scores.astype(float)

    @staticmethod
    def _normalize_scores(raw_scores: np.ndarray) -> np.ndarray:
        """Normalize scores to 0-1 range."""
        min_score = float(np.min(raw_scores))
        max_score = float(np.max(raw_scores))
        if max_score == min_score:
            return np.zeros_like(raw_scores, dtype=float)
        return (raw_scores - min_score) / (max_score - min_score)
