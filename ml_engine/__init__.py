# ml_engine/__init__.py

"""
ML Engine — Unified interface for anomaly detection, pattern recognition, and forecasting.
Fully offline, no external API calls.
"""

import pandas as pd
from typing import List, Dict, Any, Optional

from ml_engine.anomaly_detection import AnomalyDetector
from ml_engine.failure_patterns import FailurePatternDetector
from ml_engine.forecasting import Forecaster


class MLEngine:
    """
    Unified ML Engine that orchestrates:
    1. Anomaly detection (Isolation Forest + statistical)
    2. Failure pattern detection (trends, spikes, variance shifts)
    3. Forecasting (linear extrapolation + threshold projections)
    
    Usage:
        engine = MLEngine(logger=logger)
        findings = engine.execute(features_df, thresholds)
    """

    def __init__(
        self,
        contamination: float = 0.1,
        forecast_horizon: int = 10,
        logger=None,
    ):
        self.logger = logger
        self.anomaly_detector = AnomalyDetector(
            contamination=contamination,
            logger=logger,
        )
        self.pattern_detector = FailurePatternDetector(logger=logger)
        self.forecaster = Forecaster(
            horizon=forecast_horizon,
            logger=logger,
        )

    def execute(
        self,
        features_df: pd.DataFrame,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute full ML analysis pipeline.
        
        Parameters
        ----------
        features_df : pd.DataFrame
            Long-format feature data with columns:
            [run_id, feature_name, feature_value, feature_type, timestamp]
        thresholds : dict, optional
            Feature-name → threshold-value mapping for anomaly detection
        
        Returns
        -------
        list of findings from all ML modules
        """
        findings: List[Dict[str, Any]] = []

        if features_df is None or features_df.empty:
            if self.logger:
                self.logger.warning("MLEngine: No features provided, skipping")
            return findings

        if self.logger:
            self.logger.info(
                f"MLEngine: Starting analysis on {len(features_df)} feature records"
            )

        # ── Step 1: Anomaly Detection ──
        try:
            anomalies = self.anomaly_detector.detect(features_df, thresholds)
            findings.extend(anomalies)
            if self.logger:
                self.logger.info(f"  Anomaly detection: {len(anomalies)} findings")
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"  Anomaly detection failed (non-fatal): {exc}")

        # ── Step 2: Pattern Detection ──
        try:
            patterns = self.pattern_detector.detect(features_df)
            findings.extend(patterns)
            if self.logger:
                self.logger.info(f"  Pattern detection: {len(patterns)} findings")
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"  Pattern detection failed (non-fatal): {exc}")

        # ── Step 3: Forecasting ──
        try:
            forecasts = self.forecaster.forecast(features_df, thresholds)
            findings.extend(forecasts)
            if self.logger:
                self.logger.info(f"  Forecasting: {len(forecasts)} findings")
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"  Forecasting failed (non-fatal): {exc}")

        if self.logger:
            self.logger.info(
                f"MLEngine: Complete — {len(findings)} total ML findings"
            )

        return findings
