from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ml_engine.model_evaluator import ModelEvaluator


class FailureRecurrencePredictor:
    """
    Logistic model for near-term failure recurrence risk.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.model: Optional[LogisticRegression] = None

    def predict(self, signal: pd.Series) -> Optional[Dict[str, Any]]:
        clean = pd.to_numeric(signal, errors="coerce").fillna(0.0)
        if len(clean) < 20:
            return None

        frame = pd.DataFrame({"target_signal": clean})
        frame["lag_1"] = frame["target_signal"].shift(1)
        frame["lag_2"] = frame["target_signal"].shift(2)
        frame["rolling_mean_3"] = (
            frame["target_signal"].rolling(window=3, min_periods=1).mean()
        )

        threshold = float(frame["target_signal"].quantile(0.75))
        frame["y"] = (frame["target_signal"].shift(-1) > threshold).astype(int)
        frame = frame.dropna().reset_index(drop=True)

        if frame["y"].nunique() < 2 or len(frame) < 12:
            return None

        X = frame[["lag_1", "lag_2", "rolling_mean_3"]]
        y = frame["y"]

        model = LogisticRegression(
            random_state=self.random_state,
            solver="liblinear",
            max_iter=500,
        )
        model.fit(X, y)
        self.model = model

        last_row = X.iloc[[-1]]
        probability = float(model.predict_proba(last_row)[0][1])
        prediction = int(probability >= 0.5)
        confidence = ModelEvaluator.confidence_from_probability(
            probability, len(frame)
        )

        return {
            "probability": probability,
            "prediction": prediction,
            "threshold": threshold,
            "confidence": confidence,
        }
