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
            prob_pct = round(probability * 100)

            # Plain English description for failure recurrence
            if probability >= 0.75:
                severity = "CRITICAL"
                description = (
                    f"There is a high chance (roughly {prob_pct}%) that equipment which recently "
                    f"broke down will break down again in the near future. Recurring failures "
                    f"on the same equipment usually point to an unresolved root cause \u2014 "
                    f"fixing symptoms without fixing the cause leads to this pattern."
                )
                action = (
                    "For each piece of equipment that broke down more than once, "
                    "investigate and fix the underlying cause, not just the immediate symptom."
                )
            elif probability >= 0.5:
                severity = "WARNING"
                description = (
                    f"There is a moderate chance (around {prob_pct}%) that some of the recently "
                    f"failed equipment may break down again soon. This is worth monitoring closely "
                    f"to catch repeat failures before they escalate."
                )
                action = (
                    "Review equipment that has failed more than once recently and consider "
                    "scheduling preventive maintenance before the next expected failure window."
                )
            else:
                severity = "WARNING"
                description = (
                    f"The likelihood of repeat breakdowns in the near term is relatively "
                    f"low (around {prob_pct}%). Current maintenance practices appear to be "
                    f"keeping recurrence under control."
                )
                action = (
                    "Continue current maintenance schedule and keep monitoring for any "
                    "increase in repeat failure patterns."
                )

            findings.append(
                {
                    "type": "PREDICTION",
                    "feature_name": "failure_recurrence",
                    "severity": severity,
                    "confidence": float(recurrence["confidence"]),
                    "detection_method": "LogisticRegression",
                    "description": description,
                    "remediation": action,
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

            # Round for readability
            forecast_display = round(forecast_mean, 1)
            baseline_display = round(baseline, 1)

            # Plain English description for downtime forecast
            if forecast_mean > baseline * 1.15:
                severity = "WARNING"
                description = (
                    f"Based on recent breakdown trends, we expect approximately "
                    f"{forecast_display} hours of equipment downtime in the coming period. "
                    f"This is above the typical level of {baseline_display} hours and will "
                    f"impact production if not addressed through preventive action."
                )
                action = (
                    "Prioritize preventive maintenance on the highest-frequency failure "
                    "equipment this week. Review the maintenance schedule with your team."
                )
            elif forecast_mean < baseline * 0.5 or forecast_mean < 1.0:
                severity = "INFO"
                description = (
                    f"Current trends suggest downtime will remain low in the near term "
                    f"(forecast: {forecast_display} hours vs typical {baseline_display} hours). "
                    f"This is a positive sign \u2014 keep up the current maintenance practices."
                )
                action = (
                    "Continue current preventive maintenance schedule and monitor for "
                    "any changes in the downtime pattern."
                )
            else:
                severity = "INFO"
                description = (
                    f"Equipment downtime is forecast at approximately {forecast_display} hours "
                    f"for the coming period, which is in line with the recent average of "
                    f"{baseline_display} hours. No significant change expected."
                )
                action = (
                    "Maintain current maintenance schedule. No additional intervention "
                    "is needed at this time."
                )

            findings.append(
                {
                    "type": "FORECAST",
                    "feature_name": "downtime_risk",
                    "severity": severity,
                    "confidence": float(forecast["confidence"]),
                    "detection_method": "LinearRegression",
                    "description": description,
                    "remediation": action,
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

        # Plain English description for system risk
        risk_pct = round(risk * 100)
        if risk >= 0.8:
            risk_sev = "CRITICAL"
            risk_desc = (
                "Looking across all the data, the combined picture of breakdowns, "
                "downtime patterns, and failure recurrence suggests this facility is "
                "running at elevated risk. Without intervention, the frequency of "
                "breakdowns is likely to increase."
            )
            risk_action = (
                "Review the top 3 most frequently failing equipment and schedule "
                "targeted maintenance this month. Escalate to management."
            )
        elif risk >= 0.5:
            risk_sev = "WARNING"
            risk_desc = (
                f"Overall equipment health is a moderate concern (risk level: {risk_pct}%). "
                f"Some patterns in the data \u2014 such as repeat failures or rising downtime \u2014 "
                f"suggest areas that need attention before they escalate into bigger problems."
            )
            risk_action = (
                "Focus maintenance efforts on equipment showing repeat failures. "
                "Review root cause documentation and fill in any gaps."
            )
        else:
            risk_sev = "INFO"
            risk_desc = (
                "Overall, the data shows the facility is in a healthy operating state. "
                "Breakdown frequency is manageable and patterns are relatively stable."
            )
            risk_action = (
                "Maintain current maintenance schedule and monitor for any changes."
            )

        findings.append(
            {
                "type": "RISK",
                "feature_name": "system_risk",
                "severity": risk_sev,
                "confidence": float(min(max(0.55 + risk * 0.4, 0.01), 0.99)),
                "detection_method": "CompositeRisk",
                "description": risk_desc,
                "remediation": risk_action,
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
