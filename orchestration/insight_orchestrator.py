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
    
    SEVERITY_ORDER = {"CRITICAL": 3, "WARNING": 2, "INFO": 1}
    
    def __init__(self, logger=None):
        """Initialize orchestrator"""
        self.logger = logger or logging.getLogger(__name__)
    
    
    def orchestrate(self, 
                    run_id: str,
                    rule_findings: List[Dict],
                    ml_findings: List[Dict],
                    profiling_results: Optional[Dict] = None) -> List[Dict]:
        """
        Main orchestration method
        
        Args:
            run_id: Run identifier
            rule_findings: Findings from Module 3 (Rules Engine)
                          Format: List[{rule_name, affected_columns, severity, confidence, ...}]
            
            ml_findings: Findings from Module 4 (ML Engine)
                        Format: List[{type, feature_name, severity, confidence, ...}]
            
            profiling_results: Optional profiling context from Module 2
        
        Returns:
            Combined insights: List[{
                insight_id,
                run_id,
                source,  # "RULE" or "ML" or "MERGED"
                severity,
                confidence,
                feature_name / affected_columns,
                description,
                remediation,
                rule_confidence,  # If from rule
                ml_confidence,    # If from ML
                merged_confidence,
                created_at
            }]
        """
        
        self.logger.info("=" * 80)
        self.logger.info("Starting Insight Orchestration (Module 5)")
        self.logger.info("=" * 80)
        
        try:
            # STEP 1: Normalize findings
            self.logger.info("\n[1/5] Normalizing findings...")
            rule_findings = rule_findings or []
            ml_findings = ml_findings or []
            
            normalized_rules = self._normalize_rule_findings(rule_findings)
            normalized_ml = self._normalize_ml_findings(ml_findings)
            
            self.logger.info(f"      ✓ {len(normalized_rules)} rule findings normalized")
            self.logger.info(f"      ✓ {len(normalized_ml)} ML findings normalized")
            
            # STEP 2: Build resource index
            self.logger.info("\n[2/5] Building resource index...")
            resource_index = self._build_resource_index(normalized_rules, normalized_ml)
            self.logger.info(f"      ✓ {len(resource_index)} unique resources identified")
            
            # STEP 3: Merge findings by resource
            self.logger.info("\n[3/5] Merging findings by resource...")
            merged_insights = self._merge_by_resource(
                normalized_rules, 
                normalized_ml, 
                resource_index
            )
            self.logger.info(f"      ✓ {len(merged_insights)} merged insights created")
            
            # STEP 4: Apply business logic
            self.logger.info("\n[4/5] Applying orchestration logic...")
            merged_insights = self._apply_orchestration_logic(merged_insights)
            self.logger.info(f"      ✓ Orchestration logic applied")
            
            # STEP 5: Format for output
            self.logger.info("\n[5/5] Formatting for output...")
            final_insights = self._format_insights(run_id, merged_insights)
            self.logger.info(f"      ✓ {len(final_insights)} insights formatted")
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"Orchestration Complete")
            self.logger.info(f"  Total insights: {len(final_insights)}")
            self.logger.info(f"  RULE-only: {len([i for i in final_insights if i['source'] == 'RULE'])}")
            self.logger.info(f"  ML-only: {len([i for i in final_insights if i['source'] == 'ML'])}")
            self.logger.info(f"  MERGED: {len([i for i in final_insights if i['source'] == 'MERGED'])}")
            self.logger.info("=" * 80 + "\n")
            
            return final_insights
        
        except Exception as e:
            self.logger.error(f"CRITICAL orchestration error: {e}", exc_info=True)
            return []
    
    
    def _normalize_rule_findings(self, rule_findings: List[Dict]) -> List[Dict]:
        """Normalize rule findings to standard format"""
        normalized = []
        
        for finding in rule_findings:
            normalized.append({
                "source": "RULE",
                "rule_name": finding.get("rule_name", "Unknown"),
                "rule_id": finding.get("rule_id", ""),
                "triggered": finding.get("triggered", False),
                "severity": finding.get("severity", "INFO"),
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
                "severity": finding.get("severity", "INFO"),
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
                
                merged.append({
                    "resource": resource,
                    "source": "MERGED",
                    "severity": merged_severity,
                    "rule_confidence": rule_conf,
                    "ml_confidence": ml_conf,
                    "merged_confidence": blended_conf,
                    "rule_names": [r.get("rule_name") for r in rule_set],
                    "ml_types": [m.get("finding_type") for m in ml_set],
                    "message": f"Rule + ML agreement on {resource}",
                    "remediation": self._combine_remediations(rule_set),
                    "details": {"rules": rule_set, "ml": ml_set},
                })
        
        return merged
    
    
    def _escalate_severity(self, severities: List[str]) -> str:
        """Escalate severity when multiple findings present"""
        max_severity = max(
            [self.SEVERITY_ORDER.get(s, 0) for s in severities if s in self.SEVERITY_ORDER],
            default=0
        )
        
        # If any CRITICAL or if we have both WARNING and INFO, escalate
        if max_severity >= self.SEVERITY_ORDER["CRITICAL"]:
            return "CRITICAL"
        elif max_severity >= self.SEVERITY_ORDER["WARNING"] and len(severities) > 1:
            return "CRITICAL"  # Agreement escalates to CRITICAL
        elif max_severity >= self.SEVERITY_ORDER["WARNING"]:
            return "WARNING"
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
            severity = finding.get("severity", "INFO")
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
        """Generate human-readable title for insight"""
        source = finding.get("source")
        resource = finding.get("resource", "System")
        severity = finding.get("severity", "INFO")
        
        if source == "RULE":
            return f"{severity}: Rule Alert on {resource}"
        elif source == "ML":
            finding_type = finding.get("finding_type", "Anomaly")
            return f"{severity}: ML {finding_type} on {resource}"
        else:  # MERGED
            return f"{severity}: Rule + ML Agreement on {resource}"
