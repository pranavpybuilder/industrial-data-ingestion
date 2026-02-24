from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_engine.model_evaluator import ModelEvaluator


class AnomalyDetector:
    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None

    def detect(self, feature_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        if feature_matrix.empty or len(feature_matrix) < 12:
            return []

        matrix = feature_matrix.select_dtypes(include=["number"]).copy()
        if matrix.empty:
            return []

        matrix = matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=self.random_state,
        )
        model.fit(matrix)
        self.model = model

        raw_scores = -model.score_samples(matrix)  # higher = more anomalous
        preds = model.predict(matrix)  # -1 anomaly, 1 normal

        min_score = float(np.min(raw_scores))
        max_score = float(np.max(raw_scores))
        if max_score == min_score:
            normalized = np.zeros_like(raw_scores, dtype=float)
        else:
            normalized = (raw_scores - min_score) / (max_score - min_score)

        findings: List[Dict[str, Any]] = []
        for idx, (prediction, score) in enumerate(zip(preds, normalized)):
            if prediction != -1:
                continue

            row_values = matrix.iloc[idx].abs()
            top_feature = str(row_values.idxmax())
            top_value = float(matrix.iloc[idx][top_feature])

            severity = "CRITICAL" if score >= 0.8 else "WARNING"
            confidence = ModelEvaluator.confidence_from_anomaly_score(
                float(score), len(matrix)
            )
            ts = feature_matrix.index[idx]

            findings.append(
                {
                    "type": "ANOMALY",
                    "feature_name": top_feature,
                    "severity": severity,
                    "confidence": confidence,
                    "anomaly_score": float(score),
                    "detection_method": "IsolationForest",
                    "description": (
                        f"Anomalous behavior detected for '{top_feature}' "
                        f"(value={top_value:.3f}, score={score:.3f})."
                    ),
                    "current_value": top_value,
                    "timestamp": str(ts),
                }
            )

        return findings
