# rule_engine/generic_data_rules.py

"""
Generic Data Rules — Column-centric insights that work with ANY dataset.

These rules scan all numeric columns in the profiling data and generate
insights about distributions, outliers, missing data, and anomalies.
They do NOT require specific column name patterns — they work with any
data, making them ideal for industrial datasets with arbitrary feeder names.

Implements:
- DataSummaryRule:  Summarises top numeric columns (mean, range, outliers)
- HighValueRule:    Flags columns where max >> mean (spikes/outliers)
- MissingDataPatternRule:  Flags columns with significant missing data
"""

from typing import Any, Dict, List

from rule_engine.rule_base import RuleBase, RuleResult
from utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_numeric_profile(col_profile: dict) -> bool:
    """Check if a column profile represents numeric data."""
    dtype = str(col_profile.get("detected_type", "")).lower()
    if dtype in ("numeric", "float", "int", "integer", "number"):
        return True
    # Fallback: check if mean exists and is a number
    mean = col_profile.get("mean")
    return mean is not None and isinstance(mean, (int, float))


def _humanize_col(name: str) -> str:
    """Make a column name more readable for display."""
    return (
        str(name)
        .replace("_", " ")
        .replace(".", " → ")
        .title()
        .strip()
    )


def _get_numeric_columns(profile: dict) -> List[tuple]:
    """
    Extract all numeric columns from profiling data.
    Returns list of (col_name, col_profile) tuples sorted by mean descending.
    """
    numeric_cols = []
    for col_name, col_profile in profile.items():
        if not isinstance(col_profile, dict):
            continue
        if _is_numeric_profile(col_profile):
            numeric_cols.append((col_name, col_profile))

    # Sort by mean descending (most significant columns first)
    numeric_cols.sort(
        key=lambda x: abs(x[1].get("mean", 0)),
        reverse=True,
    )
    return numeric_cols


# ─────────────────────────────────────────────────────────────────────────────
# Rule 1: Data Summary
# ─────────────────────────────────────────────────────────────────────────────

class DataSummaryRule(RuleBase):
    """
    Generates a summary insight for the top numeric columns in the dataset.

    Always produces an "info" level insight listing the key columns,
    their averages, ranges, and notable statistics. This ensures the
    Insights page is never empty — it always shows what data was found.
    """

    def __init__(self, top_n: int = 8):
        super().__init__(
            name="DataSummary",
            rule_id="rule_data_summary",
            severity="info",
            default_confidence=0.95,
        )
        self.top_n = top_n

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Generate a summary of the top numeric columns."""
        profile = data.get("profile", {})
        numeric_cols = _get_numeric_columns(profile)

        if not numeric_cols:
            return self._create_result(
                triggered=True,
                message=(
                    "No numeric columns were detected in the ingested data. "
                    "This may indicate the data has only text/categorical columns, "
                    "or the header row was not detected correctly."
                ),
                remediation=(
                    "Review the uploaded file to ensure numeric data is present. "
                    "If the file has complex headers (merged cells, multi-row), "
                    "try re-uploading with a simpler format."
                ),
                affected_columns=[],
                data={"total_columns": len(profile)},
                severity="warning",
            )

        top = numeric_cols[: self.top_n]
        summaries = []
        for col_name, col_prof in top:
            mean_v = round(col_prof.get("mean", 0), 2)
            min_v = round(col_prof.get("min", 0), 2)
            max_v = round(col_prof.get("max", 0), 2)
            missing = int(col_prof.get("null_count", 0))
            label = _humanize_col(col_name)
            summaries.append(
                f"• {label}: avg {mean_v}, range [{min_v} – {max_v}]"
                + (f", {missing} missing" if missing > 0 else "")
            )

        message = (
            f"Found {len(numeric_cols)} numeric columns in the data. "
            f"Top {len(top)} columns by magnitude:\n"
            + "\n".join(summaries)
        )

        return self._create_result(
            triggered=True,
            message=message,
            remediation="",
            affected_columns=[c[0] for c in top],
            data={
                "total_numeric_columns": len(numeric_cols),
                "top_columns": [
                    {
                        "column": c[0],
                        "mean": c[1].get("mean", 0),
                        "min": c[1].get("min", 0),
                        "max": c[1].get("max", 0),
                    }
                    for c in top
                ],
            },
            severity="info",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Rule 2: High Value / Spike Detection
# ─────────────────────────────────────────────────────────────────────────────

class HighValueRule(RuleBase):
    """
    Flags numeric columns where max value is significantly higher than the mean.

    This catches spikes, outlier days, or extreme readings in any numeric
    column — not just ones named "consumption" or "kwh".
    """

    def __init__(self, spike_multiplier: float = 3.0, max_alerts: int = 5):
        super().__init__(
            name="HighValueSpike",
            rule_id="rule_high_value_spike",
            severity="warning",
            default_confidence=0.85,
        )
        self.spike_multiplier = spike_multiplier
        self.max_alerts = max_alerts

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check all numeric columns for max >> mean spikes."""
        profile = data.get("profile", {})
        numeric_cols = _get_numeric_columns(profile)

        spikes = []
        for col_name, col_prof in numeric_cols:
            mean_v = col_prof.get("mean", 0)
            max_v = col_prof.get("max", 0)
            if mean_v > 0:
                ratio = max_v / mean_v
                if ratio >= self.spike_multiplier:
                    spikes.append({
                        "column": col_name,
                        "mean": round(mean_v, 2),
                        "max": round(max_v, 2),
                        "ratio": round(ratio, 1),
                    })

        if not spikes:
            return self._not_triggered_result(self, [])

        # Take top N most extreme
        spikes.sort(key=lambda s: s["ratio"], reverse=True)
        top_spikes = spikes[: self.max_alerts]

        messages = []
        for sp in top_spikes:
            label = _humanize_col(sp["column"])
            messages.append(
                f"• {label}: peak value is {sp['ratio']}x the average "
                f"(max: {sp['max']}, avg: {sp['mean']})"
            )

        message = (
            f"Detected {len(spikes)} column(s) with extreme spikes "
            f"(peak ≥ {self.spike_multiplier}x average):\n"
            + "\n".join(messages)
        )
        remediation = (
            "Investigate the time periods when these spikes occurred. "
            "Extreme values may indicate equipment faults, unusual operations, "
            "or measurement errors. Cross-reference with operational logs."
        )

        severity = "critical" if any(s["ratio"] >= 5.0 for s in top_spikes) else "warning"

        return self._create_result(
            triggered=True,
            message=message,
            remediation=remediation,
            affected_columns=[s["column"] for s in top_spikes],
            data={"spikes": top_spikes, "total_spike_columns": len(spikes)},
            confidence=min(0.95, 0.80 + len(spikes) * 0.02),
            severity=severity,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Rule 3: Missing Data Pattern
# ─────────────────────────────────────────────────────────────────────────────

class MissingDataPatternRule(RuleBase):
    """
    Flags columns with significant missing data (>10% null values).

    Missing data in industrial datasets often indicates sensor failures,
    connectivity issues, or data collection gaps.
    """

    def __init__(self, threshold_pct: float = 10.0, max_alerts: int = 8):
        super().__init__(
            name="MissingDataPattern",
            rule_id="rule_missing_data_pattern",
            severity="warning",
            default_confidence=0.90,
        )
        self.threshold_pct = threshold_pct
        self.max_alerts = max_alerts

    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check all columns for significant missing data."""
        profile = data.get("profile", {})

        missing_cols = []
        for col_name, col_prof in profile.items():
            if not isinstance(col_prof, dict):
                continue
            null_pct = float(col_prof.get("null_percentage", 0))
            null_count = int(col_prof.get("null_count", 0))
            if null_pct >= self.threshold_pct:
                missing_cols.append({
                    "column": col_name,
                    "null_pct": round(null_pct, 1),
                    "null_count": null_count,
                })

        if not missing_cols:
            return self._not_triggered_result(self, [])

        # Sort by null percentage descending
        missing_cols.sort(key=lambda m: m["null_pct"], reverse=True)
        top = missing_cols[: self.max_alerts]

        messages = []
        for mc in top:
            label = _humanize_col(mc["column"])
            messages.append(
                f"• {label}: {mc['null_pct']}% missing ({mc['null_count']} values)"
            )

        message = (
            f"Found {len(missing_cols)} column(s) with more than "
            f"{self.threshold_pct}% missing data:\n"
            + "\n".join(messages)
        )
        remediation = (
            "Missing data may indicate sensor failures, connectivity issues, "
            "or incomplete records. Investigate the data collection process "
            "for the affected columns and consider filling gaps or flagging "
            "incomplete records."
        )

        severity = "critical" if any(m["null_pct"] > 50 for m in top) else "warning"

        return self._create_result(
            triggered=True,
            message=message,
            remediation=remediation,
            affected_columns=[m["column"] for m in top],
            data={"missing_columns": top, "total_missing": len(missing_cols)},
            confidence=0.92,
            severity=severity,
        )
