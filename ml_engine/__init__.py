from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ml_engine.anomaly_detection import AnomalyDetector
from ml_engine.failure_patterns import FailureRecurrencePredictor
from ml_engine.forecasting import DowntimeForecaster
from ml_engine.model_registry import ModelRegistry


class MLEngine:
    """
    Offline deterministic ML engine.

    Capabilities:
    - Anomaly detection (Isolation Forest)
    - Failure recurrence prediction (Logistic Regression)
    - Downtime forecasting (Linear Regression)
    - Composite risk scoring
    """

    def __init__(self, logger=None, random_state: int = 42) -> None:
        self.logger = logger
        self.random_state = random_state
        self.registry = ModelRegistry()
        self.anomaly_detector = AnomalyDetector(random_state=random_state)
        self.recurrence_predictor = FailureRecurrencePredictor(
            random_state=random_state
        )
        self.forecaster = DowntimeForecaster()

    def execute(
        self,
        features_df: pd.DataFrame,
        source_type: str,
        run_id: str,
        raw_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, Any]]:
        if features_df is None or features_df.empty:
            return []

        matrix = self._build_feature_matrix(features_df)
        if matrix.empty:
            return []

        findings: List[Dict[str, Any]] = []

        anomaly_findings = self.anomaly_detector.detect(matrix)
        findings.extend(anomaly_findings)

        downtime_signal = self._extract_downtime_signal(matrix)
        recurrence = self.recurrence_predictor.predict(downtime_signal)
        if recurrence is not None:
            probability = float(recurrence["probability"])
            findings.append(
                {
                    "type": "PREDICTION",
                    "feature_name": "failure_recurrence",
                    "severity": "CRITICAL" if probability >= 0.75 else "WARNING",
                    "confidence": float(recurrence["confidence"]),
                    "detection_method": "LogisticRegression",
                    "description": (
                        "Predicted near-term recurrence probability is "
                        f"{probability:.2%}."
                    ),
                    "current_value": probability,
                    "probability": probability,
                }
            )
            if self.recurrence_predictor.model is not None:
                self.registry.save_model(
                    run_id=run_id,
                    model_name="failure_recurrence_logistic",
                    model=self.recurrence_predictor.model,
                    metadata={
                        "source_type": source_type,
                        "probability": probability,
                        "sample_size": int(len(downtime_signal)),
                    },
                )

        forecast = self.forecaster.forecast(downtime_signal, horizon=5)
        if forecast is not None:
            forecast_mean = float(forecast["forecast_mean"])
            baseline = float(downtime_signal.mean()) if len(downtime_signal) else 0.0
            severity = "WARNING" if forecast_mean > baseline * 1.15 else "INFO"
            findings.append(
                {
                    "type": "FORECAST",
                    "feature_name": "downtime_risk",
                    "severity": severity,
                    "confidence": float(forecast["confidence"]),
                    "detection_method": "LinearRegression",
                    "description": (
                        f"Forecasted downtime mean for next window: "
                        f"{forecast_mean:.3f} (baseline: {baseline:.3f})."
                    ),
                    "current_value": forecast_mean,
                    "baseline": baseline,
                    "forecast_values": forecast["forecast_values"],
                }
            )
            if self.forecaster.model is not None:
                self.registry.save_model(
                    run_id=run_id,
                    model_name="downtime_forecast_linear",
                    model=self.forecaster.model,
                    metadata={
                        "source_type": source_type,
                        "forecast_mean": forecast_mean,
                        "baseline": baseline,
                        "r2_score": forecast["r2_score"],
                    },
                )

        risk = self._compute_risk_score(
            anomaly_findings=anomaly_findings,
            recurrence=recurrence,
            forecast=forecast,
        )
        findings.append(
            {
                "type": "RISK",
                "feature_name": "system_risk",
                "severity": "CRITICAL" if risk >= 0.8 else "WARNING" if risk >= 0.5 else "INFO",
                "confidence": float(min(max(0.55 + risk * 0.4, 0.01), 0.99)),
                "detection_method": "CompositeRisk",
                "description": f"Composite system risk score is {risk:.3f}.",
                "current_value": risk,
            }
        )

        return findings

    def _build_feature_matrix(self, features_df: pd.DataFrame) -> pd.DataFrame:
        frame = features_df.copy()
        frame["feature_value"] = pd.to_numeric(
            frame["feature_value"], errors="coerce"
        )
        frame = frame.dropna(subset=["feature_value"])

        if frame.empty:
            return pd.DataFrame()

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        if frame["timestamp"].isna().all():
            frame["timestamp"] = pd.RangeIndex(start=0, stop=len(frame), step=1)

        matrix = (
            frame.pivot_table(
                index="timestamp",
                columns="feature_name",
                values="feature_value",
                aggfunc="mean",
            )
            .sort_index()
            .replace([np.inf, -np.inf], np.nan)
            .ffill()
            .fillna(0.0)
        )
        return matrix

    def _extract_downtime_signal(self, matrix: pd.DataFrame) -> pd.Series:
        downtime_columns = [
            c
            for c in matrix.columns
            if any(token in str(c).lower() for token in ["downtime", "breakdown", "failure", "stop"])
        ]

        if downtime_columns:
            signal = matrix[downtime_columns].sum(axis=1)
        else:
            signal = matrix.mean(axis=1)

        return pd.to_numeric(signal, errors="coerce").fillna(0.0)

    def _compute_risk_score(
        self,
        anomaly_findings: List[Dict[str, Any]],
        recurrence: Optional[Dict[str, Any]],
        forecast: Optional[Dict[str, Any]],
    ) -> float:
        anomaly_component = 0.0
        if anomaly_findings:
            anomaly_component = float(
                np.mean([f.get("anomaly_score", 0.0) for f in anomaly_findings])
            )

        recurrence_component = (
            float(recurrence.get("probability", 0.0)) if recurrence else 0.0
        )
        forecast_component = 0.0
        if forecast is not None:
            values = forecast.get("forecast_values", [])
            if values:
                forecast_component = float(
                    min(max(np.mean(values) / (np.max(values) + 1e-9), 0.0), 1.0)
                )

        score = (
            anomaly_component * 0.35
            + recurrence_component * 0.4
            + forecast_component * 0.25
        )
        return float(min(max(score, 0.0), 1.0))


__all__ = ["MLEngine"]
