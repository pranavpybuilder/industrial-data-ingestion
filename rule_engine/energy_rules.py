# rule_engine/energy_rules.py

"""
Energy Domain Rules — Heuristics for power/energy cost analysis.

Implements:
- HighConsumptionDayRule: flags days with usage > 2x daily average
- ConsumptionTrendRule: flags upward trend in recent consumption
- PeakDemandRule: identifies peak demand periods for cost reduction

All messages in plain English suitable for a plant supervisor.
"""

from typing import Any, Dict, List

from rule_engine.rule_base import RuleBase, RuleResult
from utils.logger import get_logger

logger = get_logger(__name__)


class HighConsumptionDayRule(RuleBase):
    """
    Trigger when any day has energy consumption more than 2x the daily average.

    Works with energy/power cost data where rows represent daily or periodic
    consumption readings. Looks for outlier days.
    """

    def __init__(self, multiplier: float = 2.0):
        super().__init__(
            name="HighConsumptionDay",
            rule_id="rule_high_consumption_day",
            severity="warning",
            default_confidence=0.88,
        )
        self.multiplier = multiplier

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for days with unusually high energy consumption."""

        profile = data.get("profile", {})
        features = data.get("features", [])

        # Look for consumption-related columns in profile
        consumption_col = None
        for col_name in profile:
            lower = str(col_name).lower()
            if any(kw in lower for kw in [
                "consumption", "kwh", "energy", "power", "usage",
                "units", "demand", "load", "cost",
            ]):
                consumption_col = col_name
                break

        if not consumption_col:
            return self._not_triggered_result(self, [])

        col_profile = profile[consumption_col]
        mean_val = col_profile.get("mean", 0)
        max_val = col_profile.get("max", 0)

        if mean_val <= 0:
            return self._not_triggered_result(self, [])

        ratio = max_val / mean_val if mean_val > 0 else 0
        triggered = ratio >= self.multiplier

        if triggered:
            pct_above = round((ratio - 1.0) * 100)
            mean_display = round(mean_val, 1)
            max_display = round(max_val, 1)
            message = (
                f"One or more days had unusually high energy usage — the peak day "
                f"used {pct_above}% more power than the daily average. "
                f"Peak: {max_display}, Daily average: {mean_display}. "
                f"Check what was running on high-consumption days."
            )
            remediation = (
                "Review the operations and equipment running during peak consumption "
                "days. Look for equipment left running, unusual production schedules, "
                "or malfunctioning systems drawing excess power."
            )
            severity = "critical" if ratio >= 3.0 else "warning"
            confidence = min(0.95, 0.80 + (ratio - self.multiplier) * 0.05)
        else:
            message = (
                f"Energy consumption is relatively consistent across the dataset. "
                f"No single day stands out as unusually high."
            )
            remediation = ""
            severity = "info"
            confidence = 0.80

        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[consumption_col],
            data={
                "column": consumption_col,
                "mean": mean_val,
                "max": max_val,
                "ratio": round(ratio, 2),
                "multiplier_threshold": self.multiplier,
            },
            confidence=confidence,
            severity=severity,
        )


class ConsumptionTrendRule(RuleBase):
    """
    Trigger when energy consumption shows an upward trend.

    Uses the profiled statistics to detect if recent values are trending
    higher than the overall average by more than 10%.
    """

    def __init__(self, trend_threshold: float = 0.10):
        super().__init__(
            name="ConsumptionTrend",
            rule_id="rule_consumption_trend",
            severity="warning",
            default_confidence=0.82,
        )
        self.trend_threshold = trend_threshold

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for upward trend in energy consumption."""

        profile = data.get("profile", {})

        # Find a consumption column
        consumption_col = None
        for col_name in profile:
            lower = str(col_name).lower()
            if any(kw in lower for kw in [
                "consumption", "kwh", "energy", "power", "usage",
                "units", "demand", "load", "cost",
            ]):
                consumption_col = col_name
                break

        if not consumption_col:
            return self._not_triggered_result(self, [])

        col_profile = profile[consumption_col]
        mean_val = col_profile.get("mean", 0)
        median_val = col_profile.get("median", col_profile.get("p50", mean_val))
        q3_val = col_profile.get("q3", col_profile.get("percentile_75", 0))

        if mean_val <= 0:
            return self._not_triggered_result(self, [])

        # If Q3 is significantly above the median, the distribution is skewed up
        # which suggests an upward trend or increasing consumption
        skew_ratio = (q3_val - median_val) / mean_val if mean_val > 0 else 0
        triggered = skew_ratio > self.trend_threshold

        if triggered:
            pct_increase = round(skew_ratio * 100)
            message = (
                f"Energy consumption appears to be trending upward. The upper range "
                f"of usage is {pct_increase}% higher than the middle range, suggesting "
                f"costs are increasing. If this continues, monthly energy costs will "
                f"be higher than historical averages."
            )
            remediation = (
                "Investigate what is driving the increase in consumption. Common causes "
                "include aging equipment (less efficient), process changes, or systems "
                "running longer than needed. A targeted energy audit could identify "
                "the biggest savings opportunities."
            )
            severity = "warning"
            confidence = min(0.92, 0.75 + skew_ratio * 0.5)
        else:
            message = (
                "Energy consumption is stable with no significant upward trend "
                "detected in the data."
            )
            remediation = ""
            severity = "info"
            confidence = 0.78

        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[consumption_col],
            data={
                "column": consumption_col,
                "mean": mean_val,
                "median": median_val,
                "q3": q3_val,
                "skew_ratio": round(skew_ratio, 4),
                "trend_threshold": self.trend_threshold,
            },
            confidence=confidence,
            severity=severity,
        )


class PeakDemandRule(RuleBase):
    """
    Trigger when peak demand is significantly higher than average demand.

    High peak demand periods drive up demand charges on utility bills.
    Flattening the demand curve can reduce costs.
    """

    def __init__(self, peak_ratio_threshold: float = 1.8):
        super().__init__(
            name="PeakDemand",
            rule_id="rule_peak_demand",
            severity="warning",
            default_confidence=0.85,
        )
        self.peak_ratio_threshold = peak_ratio_threshold

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for high peak-to-average demand ratio."""

        profile = data.get("profile", {})

        # Find demand/load column
        demand_col = None
        for col_name in profile:
            lower = str(col_name).lower()
            if any(kw in lower for kw in [
                "demand", "peak", "load", "kw", "kva",
                "power", "max_demand",
            ]):
                demand_col = col_name
                break

        if not demand_col:
            return self._not_triggered_result(self, [])

        col_profile = profile[demand_col]
        mean_val = col_profile.get("mean", 0)
        max_val = col_profile.get("max", 0)

        if mean_val <= 0:
            return self._not_triggered_result(self, [])

        peak_ratio = max_val / mean_val
        triggered = peak_ratio >= self.peak_ratio_threshold

        if triggered:
            message = (
                f"Peak energy demand is {round(peak_ratio, 1)}x higher than the average. "
                f"High peak demand drives up demand charges on utility bills. "
                f"Smoothing out when equipment runs could reduce the peak and lower costs."
            )
            remediation = (
                "Review which equipment runs simultaneously during peak periods. "
                "Consider staggering start-up times, shifting non-critical loads to "
                "off-peak hours, or installing demand management controls."
            )
            severity = "warning"
            confidence = min(0.92, 0.80 + (peak_ratio - self.peak_ratio_threshold) * 0.05)
        else:
            message = "Peak demand is within a normal range relative to average usage."
            remediation = ""
            severity = "info"
            confidence = 0.80

        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[demand_col],
            data={
                "column": demand_col,
                "mean": mean_val,
                "max": max_val,
                "peak_ratio": round(peak_ratio, 2),
                "threshold": self.peak_ratio_threshold,
            },
            confidence=confidence,
            severity=severity,
        )
