from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ml_engine.model_evaluator import ModelEvaluator


class DowntimeForecaster:
    """
    Deterministic linear regression forecaster for downtime risk.
    """

    def __init__(self) -> None:
        self.model: Optional[LinearRegression] = None

    def forecast(
        self,
        signal: pd.Series,
        horizon: int = 5,
    ) -> Optional[Dict[str, Any]]:
        clean = pd.to_numeric(signal, errors="coerce").fillna(0.0).reset_index(drop=True)
        if len(clean) < 8:
            return None

        X = np.arange(len(clean)).reshape(-1, 1)
        y = clean.to_numpy()

        model = LinearRegression()
        model.fit(X, y)
        self.model = model

        r2 = float(model.score(X, y))
        future_x = np.arange(len(clean), len(clean) + horizon).reshape(-1, 1)
        future_pred = model.predict(future_x)

        confidence = ModelEvaluator.confidence_from_regression(r2, len(clean))
        slope = float(model.coef_[0])
        forecast_mean = float(np.mean(future_pred))

        return {
            "forecast_values": [float(v) for v in future_pred.tolist()],
            "forecast_mean": forecast_mean,
            "slope": slope,
            "r2_score": r2,
            "confidence": confidence,
        }
