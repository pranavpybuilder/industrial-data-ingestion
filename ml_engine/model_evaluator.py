from typing import Optional


class ModelEvaluator:
    """
    Heuristic confidence calibration for offline ML findings.
    """

    @staticmethod
    def confidence_from_probability(
        probability: float,
        sample_size: int,
    ) -> float:
        sample_factor = min(max(sample_size / 200.0, 0.2), 1.0)
        return float(min(max(probability * 0.8 + sample_factor * 0.2, 0.01), 0.99))

    @staticmethod
    def confidence_from_anomaly_score(
        anomaly_score: float,
        sample_size: int,
    ) -> float:
        sample_factor = min(max(sample_size / 200.0, 0.2), 1.0)
        return float(
            min(max((anomaly_score * 0.85 + sample_factor * 0.15), 0.01), 0.99)
        )

    @staticmethod
    def confidence_from_regression(
        r2_score: Optional[float],
        sample_size: int,
    ) -> float:
        if r2_score is None:
            r2_score = 0.0
        normalized_r2 = max(min((r2_score + 1.0) / 2.0, 1.0), 0.0)
        sample_factor = min(max(sample_size / 150.0, 0.2), 1.0)
        return float(
            min(max(normalized_r2 * 0.7 + sample_factor * 0.3, 0.01), 0.99)
        )
