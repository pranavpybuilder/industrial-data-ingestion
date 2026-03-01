"""
Insight Orchestrator - Module 5
Merges Rule Findings (Module 3) + ML Findings (Module 4)
Produces unified insights for Module 6 Dashboard and Module 7 Export
"""

import pandas as pd
from typing import List, Dict, Optional, Set, Tuple
import logging
from datetime import datetime


class InsightOrchestrator:
    """
    Orchestrates merging of rule-based and ML-based findings
    
    Responsibilities:
    1. Merge rule_findings and ml_findings by affected resource
    2. Deduplicate redundant findings
    3. Escalate severity when both sources flag
    4. Blend confidence scores
    5. Generate unified insights table
    """
    
    SEVERITY_ORDER = {"CRITICAL": 4, "WARNING": 3, "MEDIUM": 2, "INFO": 1}
    
    def __init__(self, logger=None):
        """Initialize orchestrator"""
        self.logger = logger or logging.getLogger(__name__)
    
    
    def orchestrate(self, 
                    run_id: str,
                    rule_findings: List[Dict],
                    ml_findings: List[Dict],
                    profiling_results: Optional[Dict] = None,
                    equipment_intelligence: Optional[Dict] = None) -> List[Dict]:
        """
        Main orchestration method
        
        Args:
            run_id: Run identifier
            rule_findings: Findings from Module 3 (Rules Engine)
            ml_findings: Findings from Module 4 (ML Engine)
            profiling_results: Optional profiling context from Module 2
            equipment_intelligence: Optional equipment-level analytics from Module 2.5
        
        Returns:
            Combined insights with sourcing and priority
        """
        
        self.logger.info("=" * 80)
        self.logger.info("Starting Insight Orchestration (Module 5)")
        self.logger.info("=" * 80)
        
        try:
            # STEP 1: Normalize findings
            self.logger.info("\n[1/5] Normalizing findings...")
            rule_findings = rule_findings or []
            ml_findings = ml_findings or []
            equipment_intelligence = equipment_intelligence or {}
            
            normalized_rules = self._normalize_rule_findings(rule_findings)
            normalized_ml = self._normalize_ml_findings(ml_findings)
            equipment_insights = self._extract_equipment_insights(equipment_intelligence)
            
            self.logger.info(
                f"      [ok] {len(normalized_rules)} rule findings normalized"
            )
            self.logger.info(
                f"      [ok] {len(normalized_ml)} ML findings normalized"
            )
            self.logger.info(
                f"      [ok] {len(equipment_insights)} equipment insights extracted"
            )
            
            # STEP 2: Build resource index
            self.logger.info("\n[2/5] Building resource index...")
            resource_index = self._build_resource_index(normalized_rules, normalized_ml)
            self.logger.info(
                f"      [ok] {len(resource_index)} unique resources identified"
            )
            
            # STEP 3: Merge findings by resource
            self.logger.info("\n[3/5] Merging findings by resource...")
            merged_insights = self._merge_by_resource(
                normalized_rules, 
                normalized_ml, 
                resource_index
            )
            self.logger.info(
                f"      [ok] {len(merged_insights)} merged insights created"
            )
            
            # STEP 4: Apply business logic
            self.logger.info("\n[4/5] Applying orchestration logic...")
            merged_insights = self._apply_orchestration_logic(merged_insights)
            self.logger.info("      [ok] Orchestration logic applied")
            
            # STEP 5: Format for output
            self.logger.info("\n[5/5] Formatting for output...")
            final_insights = self._format_insights(run_id, merged_insights)
            
            # Add equipment analysis insights
            final_insights.extend(self._format_insights(run_id, equipment_insights))
            
            self.logger.info(
                f"      [ok] {len(final_insights)} insights formatted"
            )
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"Orchestration Complete")
            self.logger.info(f"  Total insights: {len(final_insights)}")
            self.logger.info(f"  RULE-only: {len([i for i in final_insights if i['source'] == 'RULE'])}")
            self.logger.info(f"  ML-only: {len([i for i in final_insights if i['source'] == 'ML'])}")
            self.logger.info(f"  MERGED: {len([i for i in final_insights if i['source'] == 'MERGED'])}")
            self.logger.info(f"  EQUIPMENT: {len([i for i in final_insights if i['source'] == 'EQUIPMENT_ANALYSIS'])}")
            self.logger.info("=" * 80 + "\n")
            
            return final_insights
        
        except Exception as e:
            self.logger.error(f"CRITICAL orchestration error: {e}", exc_info=True)
            raise
    
    
    def _normalize_rule_findings(self, rule_findings: List[Dict]) -> List[Dict]:
        """Normalize rule findings to standard format"""
        normalized = []
        
        for finding in rule_findings:
            normalized.append({
                "source": "RULE",
                "rule_name": finding.get("rule_name", "Unknown"),
                "rule_id": finding.get("rule_id", ""),
                "triggered": finding.get("triggered", False),
                "severity": self._normalize_severity(
                    finding.get("severity", "INFO")
                ),
                "confidence": finding.get("confidence", 0.5),
                "affected_columns": finding.get("affected_columns", []),
                "affected_resource": self._extract_primary_resource(
                    finding.get("affected_columns", [])
                ),
                "message": finding.get("message", ""),
                "remediation": finding.get("remediation", ""),
                "only_if_triggered": True,
            })
        
        # Filter to triggered rules only
        return [f for f in normalized if f["triggered"]]
    
    
    def _normalize_ml_findings(self, ml_findings: List[Dict]) -> List[Dict]:
        """Normalize ML findings to standard format"""
        normalized = []
        
        for finding in ml_findings:
            finding_type = finding.get("type", "ANOMALY")
            
            normalized.append({
                "source": "ML",
                "finding_type": finding_type,  # ANOMALY, PATTERN, FORECAST
                "feature_name": finding.get("feature_name", ""),
                "affected_resource": finding.get("feature_name", ""),
                "severity": self._normalize_severity(
                    finding.get("severity", "INFO")
                ),
                "confidence": finding.get("confidence", 0.5),
                "anomaly_score": finding.get("anomaly_score", 0.0),
                "ml_method": finding.get("detection_method", "Unknown"),
                "description": finding.get("description", ""),
                "current_value": finding.get("current_value"),
                "baseline": finding.get("baseline"),
                "hours_to_threshold": finding.get("hours_to_threshold"),
            })
        
        return normalized
    
    
    def _extract_primary_resource(self, affected_columns: List[str]) -> str:
        """Extract primary resource from affected columns"""
        if not affected_columns:
            return "SYSTEM"
        
        # Try to identify resource from column names
        resource_keywords = ["temperature", "pressure", "vibration", "motor", "pump"]
        
        for col in affected_columns:
            col_lower = col.lower()
            for keyword in resource_keywords:
                if keyword in col_lower:
                    return keyword.upper()
        
        # Return first column as fallback
        return affected_columns[0].upper() if affected_columns else "SYSTEM"
    
    
    def _build_resource_index(self, 
                             rule_findings: List[Dict], 
                             ml_findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Build index mapping resources to findings"""
        index = {}
        
        for finding in rule_findings:
            resource = finding.get("affected_resource", "SYSTEM")
            if resource not in index:
                index[resource] = {"rules": [], "ml": []}
            index[resource]["rules"].append(finding)
        
        for finding in ml_findings:
            resource = finding.get("affected_resource", "SYSTEM")
            if resource not in index:
                index[resource] = {"rules": [], "ml": []}
            index[resource]["ml"].append(finding)
        
        return index
    
    
    def _merge_by_resource(self,
                          rule_findings: List[Dict],
                          ml_findings: List[Dict],
                          resource_index: Dict[str, List[Dict]]) -> List[Dict]:
        """Merge findings by resource"""
        merged = []
        
        for resource, findings_group in resource_index.items():
            rule_set = findings_group.get("rules", [])
            ml_set = findings_group.get("ml", [])
            
            # Case 1: Only rule findings
            for rule in rule_set:
                merged.append({
                    "resource": resource,
                    "source": "RULE",
                    "rule_name": rule.get("rule_name"),
                    "severity": rule.get("severity"),
                    "rule_confidence": rule.get("confidence"),
                    "ml_confidence": None,
                    "message": rule.get("message"),
                    "remediation": rule.get("remediation"),
                    "details": {"rule": rule},
                })
            
            # Case 2: Only ML findings
            for ml_finding in ml_set:
                merged.append({
                    "resource": resource,
                    "source": "ML",
                    "finding_type": ml_finding.get("finding_type"),
                    "severity": ml_finding.get("severity"),
                    "rule_confidence": None,
                    "ml_confidence": ml_finding.get("confidence"),
                    "description": ml_finding.get("description"),
                    "details": {"ml": ml_finding},
                })
            
            # Case 3: Both rule AND ML findings (merged/escalated)
            if rule_set and ml_set:
                # Create merged insight with escalated severity
                merged_severity = self._escalate_severity(
                    [r.get("severity") for r in rule_set] +
                    [m.get("severity") for m in ml_set]
                )
                
                # Blend confidence: 50% rule, 50% ML
                rule_conf = sum([r.get("confidence", 0.5) for r in rule_set]) / len(rule_set)
                ml_conf = sum([m.get("confidence", 0.5) for m in ml_set]) / len(ml_set)
                blended_conf = 0.5 * rule_conf + 0.5 * ml_conf
                
                # Build a plain English merged description
                human_resource = self._humanize_resource(resource)
                merged_desc = (
                    f"Both rule-based checks and data analysis have independently flagged "
                    f"concerns with {human_resource}. When multiple methods agree, it "
                    f"increases our confidence that this issue is real and needs attention."
                )
                merged_remed = self._combine_remediations(rule_set)
                if not merged_remed or merged_remed == "See dashboard for details":
                    merged_remed = (
                        f"Investigate {human_resource} as a priority. Multiple signals "
                        f"confirm this issue. Check recent maintenance records and "
                        f"schedule an inspection."
                    )
                merged.append({
                    "resource": resource,
                    "source": "MERGED",
                    "severity": merged_severity,
                    "rule_confidence": rule_conf,
                    "ml_confidence": ml_conf,
                    "merged_confidence": blended_conf,
                    "rule_names": [r.get("rule_name") for r in rule_set],
                    "ml_types": [m.get("finding_type") for m in ml_set],
                    "message": merged_desc,
                    "description": merged_desc,
                    "remediation": merged_remed,
                    "details": {"rules": rule_set, "ml": ml_set},
                })
        
        return merged
    
    
    def _escalate_severity(self, severities: List[str]) -> str:
        """Escalate severity when multiple findings present"""
        normalized = [self._normalize_severity(s) for s in severities]
        max_severity = max(
            [self.SEVERITY_ORDER.get(s, 0) for s in normalized if s in self.SEVERITY_ORDER],
            default=0
        )
        
        # If any CRITICAL or if we have both WARNING and INFO, escalate
        if max_severity >= self.SEVERITY_ORDER["CRITICAL"]:
            return "CRITICAL"
        elif max_severity >= self.SEVERITY_ORDER["WARNING"] and len(normalized) > 1:
            return "CRITICAL"  # Agreement escalates to CRITICAL
        elif max_severity >= self.SEVERITY_ORDER["WARNING"]:
            return "WARNING"
        elif max_severity >= self.SEVERITY_ORDER["MEDIUM"]:
            return "MEDIUM"
        else:
            return "INFO"
    
    
    def _combine_remediations(self, rule_set: List[Dict]) -> str:
        """Combine remediation actions from multiple rules"""
        remediations = [r.get("remediation", "") for r in rule_set if r.get("remediation")]
        
        if not remediations:
            return "See dashboard for details"
        
        return "; ".join(remediations[:3])  # Limit to 3 actions
    
    
    def _apply_orchestration_logic(self, merged: List[Dict]) -> List[Dict]:
        """Apply orchestration business logic"""
        
        # Sort by severity (CRITICAL > WARNING > INFO)
        def severity_key(finding):
            severity = self._normalize_severity(
                finding.get("severity", "INFO")
            )
            return self.SEVERITY_ORDER.get(severity, 0)
        
        merged.sort(key=severity_key, reverse=True)
        
        # De-duplicate similar findings
        seen = set()
        deduplicated = []
        
        for finding in merged:
            resource = finding.get("resource", "SYSTEM")
            source = finding.get("source", "RULE")
            
            # Create dedup key
            dedup_key = (resource, source)
            
            if dedup_key not in seen or finding.get("source") == "MERGED":
                deduplicated.append(finding)
                seen.add(dedup_key)
        
        return deduplicated
    
    
    def _format_insights(self, run_id: str, merged: List[Dict]) -> List[Dict]:
        """Format insights for output"""
        import uuid
        
        formatted = []
        timestamp = datetime.utcnow().isoformat()
        
        for i, finding in enumerate(merged):
            insight = {
                "insight_id": str(uuid.uuid4())[:12],
                "run_id": run_id,
                "source": finding.get("source"),
                "severity": finding.get("severity"),
                "resource": finding.get("resource"),
                "title": self._generate_title(finding),
                "description": finding.get("description") or finding.get("message", ""),
                "remediation": finding.get("remediation", ""),
                "rule_confidence": finding.get("rule_confidence"),
                "ml_confidence": finding.get("ml_confidence"),
                "merged_confidence": finding.get("merged_confidence"),
                "details": finding.get("details", {}),
                "created_at": timestamp,
            }
            
            formatted.append(insight)
        
        return formatted
    
    
    def _generate_title(self, finding: Dict) -> str:
        """Generate human-readable title for insight — plain English, NO severity prefix,
        NO algorithm names, NO variable names."""
        source = finding.get("source")
        resource = finding.get("resource", "System")
        severity = finding.get("severity", "INFO").upper()
        finding_type = finding.get("finding_type", "")

        # Humanize the resource name
        human_resource = self._humanize_resource(resource)

        if source == "RULE":
            rule_name = finding.get("rule_name", "")
            return self._title_from_rule(rule_name, human_resource, severity)
        elif source == "ML":
            return self._title_from_ml(finding_type, human_resource, severity)
        elif source == "EQUIPMENT_ANALYSIS":
            return self._title_from_equipment(finding_type, human_resource, severity)
        else:  # MERGED
            return self._title_from_merged(human_resource, severity)

    @staticmethod
    def _humanize_resource(resource: str) -> str:
        """Convert resource like 'maint__notification' to 'Maintenance Notification'."""
        if not resource or resource == "SYSTEM":
            return "Overall System"
        name = str(resource).replace("__", " ").replace("_", " ")
        abbreviations = {
            "dur": "Duration", "hrs": "Hours", "cnt": "Count",
            "maint": "Maintenance", "equip": "Equipment",
            "freq": "Frequency", "avg": "Average", "temp": "Temperature",
        }
        words = name.split()
        expanded = [abbreviations.get(w.lower(), w.capitalize()) for w in words if w]
        return " ".join(expanded) if expanded else resource

    @staticmethod
    def _title_from_rule(rule_name: str, resource: str, severity: str) -> str:
        title_map = {
            "PMOrderOverdue": "Preventive Maintenance Overdue",
            "RepeatedFailurePattern": "Repeated Equipment Failures Detected",
            "TemperatureUptrend": "Equipment Temperature Rising",
            "VibrationSpike": "High Vibration Detected",
            "EnergyAnomaly": "Energy Consumption Above Normal",
            "RFIDDataGap": "Equipment Scanner Data Gap",
            "RepeatEquipmentFailure": "Same Equipment Breaking Down Repeatedly",
            "HighMTTR": "Unusually Long Repair Times",
            "FailureEscalation": "Breakdown Frequency Increasing",
            "HighConsumptionDay": "Unusually High Energy Usage Day",
            "ConsumptionTrend": "Energy Usage Trending Upward",
        }
        if rule_name in title_map:
            return title_map[rule_name]
        # Fallback: humanize the rule name
        return rule_name.replace("_", " ").replace("Rule", "").strip() or f"Alert for {resource}"

    @staticmethod
    def _title_from_ml(finding_type: str, resource: str, severity: str) -> str:
        type_titles = {
            "ANOMALY": "Unusual Reading Detected",
            "PATTERN": "Concerning Pattern Identified",
            "FORECAST": "Downtime Forecast Update",
            "PREDICTION": "Failure Recurrence Risk",
            "RISK": "Overall Equipment Health Assessment",
        }
        return type_titles.get(str(finding_type).upper(), f"Analysis Finding for {resource}")

    @staticmethod
    def _title_from_equipment(finding_type: str, resource: str, severity: str) -> str:
        type_titles = {
            "High Risk Equipment": "Equipment at Elevated Risk",
            "Extreme Downtime": "Extended Downtime Episodes",
            "Repeat Failure": "Spare Part Replaced Multiple Times",
            "Data Quality": "Data Completeness Gap Found",
        }
        return type_titles.get(finding_type, f"{finding_type} for {resource}")

    @staticmethod
    def _title_from_merged(resource: str, severity: str) -> str:
        if severity == "CRITICAL":
            return f"Multiple Signals Confirm Issue with {resource}"
        return f"Converging Evidence for {resource}"

    def _normalize_severity(self, severity: Optional[str]) -> str:
        if not severity:
            return "INFO"

        normalized = str(severity).strip().upper()
        mapping = {
            "CRIT": "CRITICAL",
            "HIGH": "CRITICAL",
            "WARN": "WARNING",
            "NORMAL": "INFO",
            "LOW": "INFO",
        }
        normalized = mapping.get(normalized, normalized)

        if normalized not in self.SEVERITY_ORDER:
            return "INFO"
        return normalized
    
    def _extract_equipment_insights(self, equipment_intelligence: Dict) -> List[Dict]:
        """Extract high-value insights from equipment analysis"""
        
        insights = []
        
        if not equipment_intelligence:
            return insights
        
        # High-risk equipment alerts
        for eq_risk in equipment_intelligence.get("equipment_risk_scores", []):
            if eq_risk.get("risk_category") == "HIGH":
                eq_id = eq_risk.get("equipment_id", "unknown")
                insights.append({
                    "source": "EQUIPMENT_ANALYSIS",
                    "severity": "WARNING",
                    "resource": eq_id,
                    "finding_type": "High Risk Equipment",
                    "description": (
                        f"Equipment '{eq_id}' is showing a pattern of breakdowns and "
                        f"downtime that places it in the high-risk category. This equipment "
                        f"is more likely than others to fail again in the near term."
                    ),
                    "remediation": (
                        eq_risk.get("recommendation", "") or
                        f"Schedule a thorough inspection of equipment '{eq_id}' and "
                        f"implement preventive maintenance before the next expected failure."
                    ),
                    "confidence": eq_risk.get("risk_score", 0),
                })

        # Extreme downtime alerts
        downtime = equipment_intelligence.get("downtime_analysis", {})
        extreme_count = downtime.get("extreme_events_count", 0)
        threshold_hrs = downtime.get("extreme_threshold_hours", 0)
        if extreme_count > 0:
            insights.append({
                "source": "EQUIPMENT_ANALYSIS",
                "severity": "WARNING",
                "resource": "Downtime",
                "finding_type": "Extreme Downtime",
                "description": (
                    f"{extreme_count} breakdown(s) took an unusually long time to resolve "
                    f"\u2014 each exceeding {threshold_hrs} hours. Extended downtime events "
                    f"have a disproportionate impact on production and should be investigated "
                    f"for ways to speed up the repair process."
                ),
                "remediation": (
                    "Investigate why these breakdowns took so long to resolve. Consider "
                    "pre-staging critical spare parts, improving technician response times, "
                    "or redesigning the maintenance process for this equipment type."
                ),
                "confidence": 0.85,
            })

        # Repeat spare failure alerts
        for spare_alert in equipment_intelligence.get("spare_patterns", {}).get("repeat_failure_alerts", []):
            spare_name = spare_alert.get("spare", "unknown part")
            replace_count = spare_alert.get("replacement_count", 0)
            insights.append({
                "source": "EQUIPMENT_ANALYSIS",
                "severity": "MEDIUM",
                "resource": spare_name,
                "finding_type": "Repeat Failure",
                "description": (
                    f"The spare part '{spare_name}' has been replaced {replace_count} times. "
                    f"Repeated replacements of the same part often indicate an underlying "
                    f"problem that is not being addressed \u2014 such as misalignment, "
                    f"overloading, or a defective batch of parts."
                ),
                "remediation": (
                    f"Investigate why '{spare_name}' keeps failing. Check for root causes "
                    f"like misalignment, overloading, or environmental factors. Consider "
                    f"upgrading to a more durable alternative."
                ),
                "confidence": 0.75,
            })

        # Data quality alerts
        for quality_issue in equipment_intelligence.get("data_quality", {}).get("quality_issues", []):
            if quality_issue.get("severity") == "High":
                issue_type = quality_issue.get("issue_type", "Data gap")
                pct = quality_issue.get("percentage", 0)
                pct_display = round(pct)
                insights.append({
                    "source": "EQUIPMENT_ANALYSIS",
                    "severity": "INFO",
                    "resource": "Documentation",
                    "finding_type": "Data Quality",
                    "description": (
                        f"{issue_type} \u2014 approximately {pct_display}% of records are affected. "
                        f"Incomplete data makes it harder to identify root causes and predict "
                        f"future failures. Improving data quality will directly improve the "
                        f"accuracy of these analyses."
                    ),
                    "remediation": (
                        "Require all fields to be completed when logging breakdowns. "
                        "Review past records and fill in missing information where possible."
                    ),
                    "confidence": 0.80,
                })
        
        return insights
