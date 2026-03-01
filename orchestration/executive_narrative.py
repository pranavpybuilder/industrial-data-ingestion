from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

import pandas as pd


@dataclass(frozen=True)
class NarrativeScores:
    risk_score: float
    machine_health_score: float
    system_maturity_score: float
    prediction_confidence: float


class ExecutiveNarrativeComposer:
    """
    Deterministic executive narrative synthesis.
    No LLM calls, no randomness, and fully offline.

    All outputs are in plain English suitable for a plant manager or supervisor.
    No variable names, no algorithm names, no raw decimal scores.
    """

    def compose(
        self,
        run_id: str,
        source_type: str,
        raw_df: pd.DataFrame,
        unified_insights: List[Dict[str, Any]],
        rule_findings: List[Dict[str, Any]],
        ml_findings: List[Dict[str, Any]],
        profiling_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        metrics = self._build_metrics(raw_df, unified_insights, ml_findings, profiling_result)
        scores = self._build_scores(metrics)

        verdict_label = self._risk_label(scores.risk_score)
        decision = self._build_decision(scores, metrics)
        critical_alerts = self._build_critical_alerts(unified_insights)
        machine_intelligence = self._build_machine_intelligence(metrics)
        predictive_insights = self._build_predictive_insights(ml_findings, scores)
        opportunities = self._build_optimization_opportunities(metrics, scores)

        # Build a proper paragraph executive summary — NOT machine format
        exec_summary = self._build_executive_summary(metrics, scores, verdict_label)

        return {
            "run_id": run_id,
            "source_type": source_type,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": exec_summary,
            "sections": {
                "Executive Summary": exec_summary,
                "Key Decision Insight": decision,
                "Core Metrics": metrics,
                "Critical Alerts": critical_alerts,
                "Machine Intelligence": machine_intelligence,
                "Predictive Insights": predictive_insights,
                "Optimization Opportunities": opportunities,
                "System Verdict": {
                    "verdict": self._verdict_text(scores),
                    "risk_score": round(scores.risk_score, 4),
                    "machine_health_score": round(scores.machine_health_score, 2),
                    "system_maturity_score": round(scores.system_maturity_score, 2),
                    "prediction_confidence": round(scores.prediction_confidence, 4),
                },
            },
        }

    def _build_executive_summary(
        self,
        metrics: Dict[str, Any],
        scores: NarrativeScores,
        verdict_label: str,
    ) -> str:
        """Build a proper paragraph executive summary in plain English."""
        row_count = metrics.get("row_count", 0)
        breakdown_freq = metrics.get("breakdown_frequency", 0)
        downtime_hours = metrics.get("downtime_total_hours", 0.0)
        critical_count = metrics.get("critical_alert_count", 0)
        warning_count = metrics.get("warning_alert_count", 0)
        total_insights = metrics.get("total_insights", 0)
        root_cause_pct = metrics.get("root_cause_completeness_pct", 0.0)
        repeat_machines = metrics.get("repeat_machine_count", 0)

        parts = []

        # Opening sentence
        parts.append(
            f"This analysis reviewed {row_count} records and identified "
            f"{total_insights} areas of concern."
        )

        # Most urgent finding
        if critical_count > 0:
            parts.append(
                f"The most urgent finding requires immediate attention \u2014 "
                f"{critical_count} item(s) have been flagged as needing action now."
            )

        # Downtime context
        if downtime_hours > 0:
            parts.append(
                f"Total recorded downtime across the dataset is approximately "
                f"{round(downtime_hours, 1)} hours."
            )

        # Repeat failures
        if repeat_machines > 0:
            parts.append(
                f"There are {repeat_machines} piece(s) of equipment that have experienced "
                f"breakdowns more than once, suggesting root causes may not be fully resolved."
            )

        # Root cause gaps
        if root_cause_pct < 70:
            parts.append(
                f"Root cause documentation is incomplete \u2014 only {round(root_cause_pct)}% "
                f"of breakdown records have a root cause recorded. Without this information, "
                f"it is difficult to prevent repeat failures."
            )

        # Risk verdict
        if scores.risk_score >= 0.8:
            parts.append(
                "Overall, the facility is running at elevated risk and requires "
                "immediate corrective action to prevent further breakdowns."
            )
        elif scores.risk_score >= 0.5:
            parts.append(
                "Immediate priorities are reviewing the flagged records, scheduling "
                "preventive maintenance on top-failing equipment, and improving root "
                "cause documentation across all breakdown reports."
            )
        else:
            parts.append(
                "The facility is in a manageable state. Continue current maintenance "
                "practices and monitor the key indicators highlighted in this report."
            )

        return " ".join(parts)

    def build_narrative_insight(
        self,
        run_id: str,
        narrative: Dict[str, Any],
    ) -> Dict[str, Any]:
        verdict = narrative["sections"]["System Verdict"]
        risk_score = float(verdict.get("risk_score", 0.0))
        severity = "CRITICAL" if risk_score >= 0.8 else "WARNING" if risk_score >= 0.5 else "INFO"
        priority_tier = "IMMEDIATE" if severity == "CRITICAL" else "HIGH" if severity == "WARNING" else "LOW"

        return {
            "insight_id": str(uuid.uuid4())[:12],
            "run_id": run_id,
            "source": "EXECUTIVE",
            "severity": severity,
            "resource": "SYSTEM",
            "title": "Executive Intelligence Summary",
            "description": narrative["sections"]["Executive Summary"],
            "remediation": narrative["sections"]["Key Decision Insight"],
            "priority_score": risk_score,
            "priority_rank": 1,
            "priority_tier": priority_tier,
            "needs_action": severity in {"CRITICAL", "WARNING"},
            "action_type": "ALERT" if severity == "CRITICAL" else "INVESTIGATE" if severity == "WARNING" else "MONITOR",
            "details": {"executive_narrative": narrative},
        }

    def _build_metrics(
        self,
        raw_df: pd.DataFrame,
        unified_insights: List[Dict[str, Any]],
        ml_findings: List[Dict[str, Any]],
        profiling_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        frame = raw_df.copy() if raw_df is not None else pd.DataFrame()
        row_count = int(len(frame))

        breakdown = self._pick_numeric_series(
            frame,
            candidates=["breakdown_count", "failure_count", "breakdown"],
            default=float(1.0),
        )
        breakdown_frequency = int(round(float(breakdown.sum()))) if row_count else 0

        downtime = self._pick_numeric_series(
            frame,
            candidates=["downtime_hours", "downtime", "breakdown_dur", "duration_hours"],
            default=float(0.0),
        )
        downtime_total = float(downtime.sum()) if row_count else 0.0
        avg_downtime = float(downtime_total / max(breakdown_frequency, 1)) if row_count else 0.0

        failure_distribution = self._distribution_percent(frame, "failure_type", top_n=5)
        repeat_machines = self._repeat_count(frame, "equipment_id")
        root_cause_completeness = self._completeness_percent(frame, "root_cause")
        technician_workload = self._distribution_percent(frame, "technician", top_n=5)
        reactive_count, preventive_count = self._maintenance_mix(frame)
        total_maint = reactive_count + preventive_count
        preventive_ratio = float(preventive_count / max(total_maint, 1))
        reactive_ratio = float(reactive_count / max(total_maint, 1))

        risk_score = self._extract_risk_score(ml_findings, unified_insights)
        ml_prediction_confidence = self._extract_prediction_confidence(ml_findings)
        critical_alert_count = len(
            [ins for ins in unified_insights if str(ins.get("severity", "")).upper() == "CRITICAL"]
        )
        warning_count = len(
            [ins for ins in unified_insights if str(ins.get("severity", "")).upper() == "WARNING"]
        )

        health_score = 0.0
        if isinstance(profiling_result, dict):
            health_score = float(profiling_result.get("health_score", 0.0))

        return {
            "row_count": row_count,
            "breakdown_frequency": breakdown_frequency,
            "downtime_total_hours": round(downtime_total, 4),
            "avg_downtime_hours": round(avg_downtime, 4),
            "failure_type_distribution_pct": failure_distribution,
            "repeat_machine_count": repeat_machines,
            "root_cause_completeness_pct": round(root_cause_completeness, 2),
            "technician_workload": technician_workload,
            "reactive_count": reactive_count,
            "preventive_count": preventive_count,
            "reactive_ratio": round(reactive_ratio, 4),
            "preventive_ratio": round(preventive_ratio, 4),
            "risk_score": round(risk_score, 4),
            "ml_prediction_confidence": round(ml_prediction_confidence, 4),
            "data_health_score": round(health_score, 2),
            "critical_alert_count": critical_alert_count,
            "warning_alert_count": warning_count,
            "total_insights": len(unified_insights),
        }

    def _build_scores(self, metrics: Dict[str, Any]) -> NarrativeScores:
        risk_score = float(metrics.get("risk_score", 0.0))
        critical_ratio = float(metrics.get("critical_alert_count", 0)) / max(
            int(metrics.get("total_insights", 0)), 1
        )
        machine_health = 1.0 - min(max((risk_score * 0.6) + (critical_ratio * 0.4), 0.0), 1.0)

        root_cause = float(metrics.get("root_cause_completeness_pct", 0.0)) / 100.0
        preventive = float(metrics.get("preventive_ratio", 0.0))
        data_health = float(metrics.get("data_health_score", 0.0)) / 100.0
        maturity = (0.4 * root_cause) + (0.35 * preventive) + (0.25 * data_health)

        prediction_confidence = float(metrics.get("ml_prediction_confidence", 0.0))
        if prediction_confidence <= 0:
            prediction_confidence = min(max(0.45 + risk_score * 0.4, 0.01), 0.99)

        return NarrativeScores(
            risk_score=min(max(risk_score, 0.0), 1.0),
            machine_health_score=min(max(machine_health * 100.0, 0.0), 100.0),
            system_maturity_score=min(max(maturity * 100.0, 0.0), 100.0),
            prediction_confidence=min(max(prediction_confidence, 0.01), 0.99),
        )

    def _build_decision(self, scores: NarrativeScores, metrics: Dict[str, Any]) -> str:
        if scores.risk_score >= 0.8:
            return (
                "Immediate intervention is required. Prioritize high-risk equipment, "
                "schedule urgent maintenance, and review all critical findings today."
            )
        if scores.risk_score >= 0.5:
            return (
                "There are several areas that need attention soon. Focus on equipment "
                "with repeat failures and make sure root cause documentation is complete "
                "for all recent breakdowns."
            )
        return (
            "The situation is under control. Continue your current maintenance schedule, "
            "keep an eye on the trends highlighted in this report, and ensure your team "
            "documents root causes for every breakdown."
        )

    def _build_critical_alerts(self, unified_insights: List[Dict[str, Any]]) -> List[str]:
        critical = [
            ins.get("description") or ins.get("title") or "Critical alert detected."
            for ins in unified_insights
            if str(ins.get("severity", "")).upper() == "CRITICAL"
        ]
        if critical:
            return critical[:5]
        return ["No critical alerts for this analysis."]

    def _build_machine_intelligence(self, metrics: Dict[str, Any]) -> List[str]:
        items = []
        repeat = metrics.get("repeat_machine_count", 0)
        if repeat > 0:
            items.append(
                f"{repeat} piece(s) of equipment have experienced breakdowns more than once."
            )
        else:
            items.append("No repeat breakdowns detected on the same equipment.")

        root_pct = metrics.get("root_cause_completeness_pct", 0.0)
        if root_pct < 70:
            items.append(
                f"Root cause documentation is only {round(root_pct)}% complete. "
                f"Improving this will help prevent repeat failures."
            )
        else:
            items.append(
                f"Root cause documentation is {round(root_pct)}% complete \u2014 good practice."
            )

        reactive = metrics.get("reactive_count", 0)
        preventive = metrics.get("preventive_count", 0)
        if reactive > 0 or preventive > 0:
            items.append(
                f"Maintenance is split {reactive} reactive vs {preventive} preventive actions."
            )

        return items

    def _build_predictive_insights(
        self,
        ml_findings: List[Dict[str, Any]],
        scores: NarrativeScores,
    ) -> List[str]:
        predictive = []
        for finding in ml_findings:
            ftype = str(finding.get("type", "")).upper()
            if ftype not in {"PREDICTION", "FORECAST", "RISK"}:
                continue
            desc = str(finding.get("description", "")).strip()
            if desc:
                predictive.append(desc)

        if not predictive:
            label = self._risk_label(scores.risk_score).lower()
            predictive = [
                f"The analysis indicates a {label} risk trajectory. "
                f"Continue monitoring key indicators for any changes."
            ]
        return predictive[:5]

    def _build_optimization_opportunities(
        self,
        metrics: Dict[str, Any],
        scores: NarrativeScores,
    ) -> List[str]:
        opportunities: List[str] = []

        if float(metrics.get("root_cause_completeness_pct", 0.0)) < 80.0:
            opportunities.append(
                "Improve root cause documentation on breakdown records. Without knowing "
                "why failures happen, it is impossible to prevent them from recurring."
            )
        if float(metrics.get("preventive_ratio", 0.0)) < 0.45:
            opportunities.append(
                "Shift maintenance strategy toward more preventive work, especially "
                "on equipment that has broken down more than once."
            )
        if float(metrics.get("avg_downtime_hours", 0.0)) > 2.0:
            opportunities.append(
                "Reduce average repair time by pre-staging critical spare parts "
                "and ensuring technicians are assigned before breakdowns occur."
            )
        if scores.risk_score >= 0.6:
            opportunities.append(
                "Create a watchlist of high-risk equipment and set up regular "
                "inspections to catch problems before they become breakdowns."
            )

        if not opportunities:
            opportunities.append(
                "Current practices are solid. Maintain your maintenance schedule and "
                "continue monitoring the indicators in this report."
            )
        return opportunities

    def _verdict_text(self, scores: NarrativeScores) -> str:
        if scores.risk_score >= 0.8:
            return "The facility needs immediate corrective action to reduce breakdown risk."
        if scores.risk_score >= 0.5:
            return "There are areas of concern that need targeted attention soon."
        return "The facility is operating within acceptable parameters."

    @staticmethod
    def _pick_numeric_series(
        frame: pd.DataFrame,
        candidates: List[str],
        default: float,
    ) -> pd.Series:
        if frame is None or frame.empty:
            return pd.Series([], dtype="float64")

        col_map = {
            str(column).strip().lower(): str(column)
            for column in frame.columns
        }
        for candidate in candidates:
            source = col_map.get(candidate.lower())
            if source is None:
                continue
            values = pd.to_numeric(frame[source], errors="coerce")
            if values.notna().sum() > 0:
                return values.fillna(default)

        return pd.Series([default] * len(frame), index=frame.index, dtype="float64")

    @staticmethod
    def _distribution_percent(
        frame: pd.DataFrame,
        column_name: str,
        top_n: int,
    ) -> Dict[str, float]:
        if frame is None or frame.empty or column_name not in frame.columns:
            return {}
        values = (
            frame[column_name]
            .astype("string")
            .fillna("unknown")
            .str.strip()
            .replace("", "unknown")
        )
        dist = values.value_counts(normalize=True).head(top_n)
        return {
            str(name): round(float(value * 100.0), 2)
            for name, value in dist.items()
        }

    @staticmethod
    def _repeat_count(frame: pd.DataFrame, column_name: str) -> int:
        if frame is None or frame.empty or column_name not in frame.columns:
            return 0
        values = frame[column_name].astype("string").fillna("").str.strip()
        counts = values[values != ""].value_counts()
        return int((counts > 1).sum())

    @staticmethod
    def _completeness_percent(frame: pd.DataFrame, column_name: str) -> float:
        if frame is None or frame.empty or column_name not in frame.columns:
            return 0.0
        non_null = frame[column_name].astype("string").fillna("").str.strip() != ""
        return float(non_null.mean() * 100.0)

    @staticmethod
    def _maintenance_mix(frame: pd.DataFrame) -> Tuple[int, int]:
        if frame is None or frame.empty or "maintenance_type" not in frame.columns:
            return 0, 0
        values = frame["maintenance_type"].astype("string").fillna("").str.upper()
        preventive = values.str.contains("PM|PREVENT|SCHEDULE", regex=True).sum()
        total = int((values.str.strip() != "").sum())
        preventive_count = int(preventive)
        reactive_count = int(max(total - preventive_count, 0))
        return reactive_count, preventive_count

    @staticmethod
    def _extract_risk_score(
        ml_findings: List[Dict[str, Any]],
        unified_insights: List[Dict[str, Any]],
    ) -> float:
        for finding in ml_findings:
            if str(finding.get("type", "")).upper() != "RISK":
                continue
            value = pd.to_numeric([finding.get("current_value")], errors="coerce")[0]
            if pd.notna(value):
                return float(min(max(value, 0.0), 1.0))

        if not unified_insights:
            return 0.0
        max_priority = max(float(ins.get("priority_score", 0.0)) for ins in unified_insights)
        return float(min(max(max_priority, 0.0), 1.0))

    @staticmethod
    def _extract_prediction_confidence(ml_findings: List[Dict[str, Any]]) -> float:
        values: List[float] = []
        for finding in ml_findings:
            ftype = str(finding.get("type", "")).upper()
            if ftype not in {"PREDICTION", "FORECAST", "RISK"}:
                continue
            value = pd.to_numeric([finding.get("confidence")], errors="coerce")[0]
            if pd.notna(value):
                values.append(float(value))
        if not values:
            return 0.0
        return float(sum(values) / len(values))

    @staticmethod
    def _risk_label(risk_score: float) -> str:
        if risk_score >= 0.8:
            return "HIGH"
        if risk_score >= 0.5:
            return "ELEVATED"
        return "CONTROLLED"
