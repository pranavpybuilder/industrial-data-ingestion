# rule_engine/explainability.py

"""
Rule Explainability - Generate human-readable explanations for findings.

Provides:
- Context-aware message generation
- Action recommendations
- Severity explanations
- Confidence justifications
"""

from typing import Dict, Any, List
from rule_engine.rule_base import RuleResult, Severity
from utils.logger import get_logger

logger = get_logger(__name__)


class RuleExplainer:
    """Convert rule results into clear, actionable explanations."""
    
    # Message templates for different rule types
    RULE_TEMPLATES = {
        "ParameterOutOfRange": {
            "critical": "CRITICAL: {column} value {value:.2f} far exceeds safe limit of {limit}. {machine_type} at {risk_type} risk.",
            "warning": "WARNING: {column} value {value:.2f} exceeds recommended limit of {limit}. Monitor closely.",
            "action": "Check {column} readings immediately. Verify sensor calibration. Assess equipment condition.",
        },
        "MissingData": {
            "critical": "CRITICAL: {column} data is {missing_pct:.0%} incomplete. Insufficient data for analysis.",
            "warning": "WARNING: {column} has {missing_pct:.0%} missing values. Data quality degraded.",
            "action": "Verify data source {source}. Check sensor connectivity. Review collection interval.",
        },
        "OutlierDetection": {
            "critical": "CRITICAL: {outlier_count} extreme outliers detected in {column} ({outlier_pct:.1%}). Indicates process deviation.",
            "warning": "WARNING: {outlier_count} anomalous values in {column}. Investigate cause.",
            "action": "Review {outlier_count} suspect readings. Verify measurement accuracy. Check for process changes.",
        },
        "PMOrderOverdue": {
            "critical": "CRITICAL: {overdue_count} PM orders overdue by {max_days} days. Maintenance severely delayed.",
            "warning": "WARNING: {overdue_count} PM orders pending. Equipment due for maintenance.",
            "action": "Schedule preventive maintenance immediately. Update PM calendar. Assign technician.",
        },
        "RepeatedFailurePattern": {
            "critical": "CRITICAL: Equipment failed {failure_count} times. Chronic issue requires investigation.",
            "warning": "WARNING: {failure_count} failures detected. Pattern emerging.",
            "action": "Conduct root-cause analysis. Review failure history. Consider component replacement.",
        },
        "TemperatureUptrend": {
            "warning": "WARNING: Operating temperature trending upward ({current:.1f}°C, approaching {max:.1f}°C limit).",
            "action": "Monitor temperature closely. Check for fouling, blockage, or bearing wear. Plan maintenance.",
        },
        "VibrationSpike": {
            "critical": "CRITICAL: Vibration at {max_vib:.2f} mm/s FAR exceeds safe limit. Bearing failure imminent!",
            "warning": "WARNING: Vibration elevated at {max_vib:.2f} mm/s. Bearing wear suspected.",
            "action": "URGENT: Reduce load or stop equipment. Inspect bearings immediately. Plan replacement.",
        },
        "EnergyAnomaly": {
            "warning": "WARNING: Energy consumption increased {drop_pct:.0%} above baseline. Efficiency degraded.",
            "action": "Check for mechanical friction. Review operating conditions. Schedule efficiency audit.",
        },
        "RFIDDataGap": {
            "warning": "WARNING: RFID scanner gap detected. No scans for {gap_hours} hours.",
            "action": "Verify scanner power/connectivity. Check network. Review scan history logs.",
        },
    }
    
    SEVERITY_EXPLANATIONS = {
        "critical": "Requires immediate action. Equipment or process at risk.",
        "warning": "Investigate and monitor. Potential issue developing.",
        "info": "Informational. No immediate action needed.",
    }
    
    @classmethod
    def explain_result(cls, result: RuleResult, context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Generate comprehensive explanation for a rule result.
        
        Parameters
        ----------
        result : RuleResult
            Rule evaluation result
        context : dict, optional
            Additional context (machine_type, source, etc.)
        
        Returns
        -------
        dict with keys:
            - "finding": What was detected
            - "severity_desc": Why it matters
            - "action": Recommended next step
            - "timeline": Urgency
        """
        
        context = context or {}
        
        finding = cls._format_finding(result, context)
        severity_desc = cls.SEVERITY_EXPLANATIONS.get(result.severity, "Unknown severity")
        action = cls._format_action(result, context)
        timeline = cls._format_timeline(result.severity)
        
        return {
            "finding": finding,
            "severity_description": severity_desc,
            "recommended_action": action,
            "urgency": timeline,
            "confidence": f"{result.confidence:.0%} confidence",
            "affected_areas": ", ".join(result.affected_columns) if result.affected_columns else "N/A",
        }
    
    @classmethod
    def _format_finding(cls, result: RuleResult, context: Dict[str, Any]) -> str:
        """Format the core finding message."""
        
        if not result.triggered:
            return f"✓ {result.message}"
        
        # Try to use template, fall back to message
        rule_name = result.rule_name.split("(")[0]  # Remove column names
        templates = cls.RULE_TEMPLATES.get(rule_name, {})
        template = templates.get(result.severity, result.message)
        
        try:
            # Merge result data with context
            format_data = {**result.data, **context}
            formatted = template.format(**format_data)
        except KeyError:
            formatted = result.message
        
        return formatted
    
    @classmethod
    def _format_action(cls, result: RuleResult, context: Dict[str, Any]) -> str:
        """Format recommended action."""
        
        if not result.triggered:
            return "No action required. Continue monitoring."
        
        # Use custom remediation or template
        if result.remediation:
            return result.remediation
        
        rule_name = result.rule_name.split("(")[0]
        templates = cls.RULE_TEMPLATES.get(rule_name, {})
        action_template = templates.get("action", "Review and investigate.")
        
        try:
            format_data = {**result.data, **context}
            formatted = action_template.format(**format_data)
        except KeyError:
            formatted = action_template
        
        return formatted
    
    @classmethod
    def _format_timeline(cls, severity: str) -> str:
        """Translate severity to urgency timeline."""
        
        timeline_map = {
            "critical": "Within hours",
            "warning": "Within 24-48 hours",
            "info": "Ongoing monitoring",
        }
        
        return timeline_map.get(severity, "Assess schedule")
    
    @classmethod
    def explain_batch_results(cls, 
                             results: List[RuleResult],
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate summary explanation for multiple results.
        
        Parameters
        ----------
        results : list of RuleResult
            Multiple rule evaluation results
        context : dict, optional
            Additional context
        
        Returns
        -------
        dict with summary statistics and prioritized findings
        """
        
        context = context or {}
        
        triggered = [r for r in results if r.triggered]
        critical = [r for r in triggered if r.severity == "critical"]
        warnings = [r for r in triggered if r.severity == "warning"]
        info = [r for r in results if r.severity == "info"]
        
        # Prioritize by severity then confidence
        prioritized = sorted(
            triggered,
            key=lambda r: (
                0 if r.severity == "critical" else 1 if r.severity == "warning" else 2,
                -r.confidence  # Higher confidence first
            )
        )
        
        summary = {
            "total_rules_checked": len(results),
            "triggered_findings": len(triggered),
            "critical_findings": len(critical),
            "warnings": len(warnings),
            "ok_checks": len(results) - len(triggered),
            "overall_status": cls._determine_overall_status(critical, warnings),
            "findings_by_priority": [
                {
                    "rule": r.rule_name,
                    "severity": r.severity,
                    "message": r.message,
                    "action": r.remediation or "Investigate",
                    "confidence": f"{r.confidence:.0%}",
                }
                for r in prioritized[:10]  # Top 10 findings
            ],
        }
        
        if critical:
            summary["critical_actions"] = [
                f"• {r.remediation or r.message}" for r in critical
            ]
        
        return summary
    
    @classmethod
    def _determine_overall_status(cls, critical: List[RuleResult], warnings: List[RuleResult]) -> str:
        """Determine overall system status."""
        
        if critical:
            return f"CRITICAL: {len(critical)} urgent issue(s)"
        elif warnings:
            return f"WARNING: {len(warnings)} issue(s) detected"
        else:
            return "NORMAL: All checks passed"
    
    @classmethod
    def generate_report(cls, 
                       results: List[RuleResult],
                       run_id: str,
                       context: Dict[str, Any] = None) -> str:
        """
        Generate human-readable text report.
        
        Parameters
        ----------
        results : list of RuleResult
            Rule evaluation results
        run_id : str
            Run identifier
        context : dict, optional
            Additional context (source_type, file_name, etc.)
        
        Returns
        -------
        str: Formatted report text
        """
        
        context = context or {}
        summary = cls.explain_batch_results(results, context)
        
        report = []
        report.append("=" * 70)
        report.append(f"MAINTENANCE RULE ANALYSIS REPORT")
        report.append(f"Run ID: {run_id}")
        report.append(f"Source: {context.get('source_type', 'Unknown')}")
        report.append("=" * 70)
        report.append("")
        
        # Overall status
        report.append(f"Status: {summary['overall_status']}")
        report.append(f"Checks: {summary['total_rules_checked']} rules evaluated")
        report.append(f"Triggered: {summary['triggered_findings']} findings")
        report.append("")
        
        # Critical actions
        if "critical_actions" in summary:
            report.append("CRITICAL ACTIONS REQUIRED:")
            for action in summary["critical_actions"]:
                report.append(f"  {action}")
            report.append("")
        
        # Top findings
        if summary["findings_by_priority"]:
            report.append("TOP FINDINGS:")
            for i, finding in enumerate(summary["findings_by_priority"], 1):
                severity_symbol = "🔴" if finding["severity"] == "critical" else "🟡" if finding["severity"] == "warning" else "🟢"
                report.append(f"  {i}. [{finding['severity'].upper()}] {finding['rule']}")
                report.append(f"     {finding['message']}")
                report.append(f"     Action: {finding['action']}")
                report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)
