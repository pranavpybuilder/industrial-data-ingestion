"""
Prioritization Module - Module 5
Prioritizes insights for dashboard display and action
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime


class InsightPrioritizer:
    """
    Prioritizes insights for:
    1. Dashboard display
    2. Alert notifications
    3. Maintenance action queue
    4. Resource allocation
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    
    def prioritize(self, insights: List[Dict]) -> List[Dict]:
        """
        Assign priority tiers and action flags
        
        Returns insights with:
        - tier (IMMEDIATE, HIGH, MEDIUM, LOW)
        - needs_action (bool)
        - action_type (ALERT, INVESTIGATE, MONITOR, RESOLVE)
        """
        
        for insight in insights:
            severity = self._normalize_severity(
                insight.get("severity", "INFO")
            )
            insight["severity"] = severity
            source = insight.get("source", "RULE")
            priority_score = insight.get("priority_score", 0.5)
            
            # Assign tier
            if severity == "CRITICAL":
                tier = "IMMEDIATE"
            elif severity == "WARNING" and priority_score > 0.7:
                tier = "HIGH"
            elif severity == "WARNING":
                tier = "MEDIUM"
            elif severity == "MEDIUM":
                tier = "MEDIUM"
            else:
                tier = "LOW"
            
            # Determine if action is needed
            needs_action = severity in ["CRITICAL", "WARNING", "MEDIUM"]
            
            # Assign action type
            if source == "MERGED":
                # High confidence agreement between rule and ML
                action_type = "ALERT"
            elif severity == "CRITICAL":
                action_type = "ALERT"
            elif severity == "WARNING":
                action_type = "INVESTIGATE"
            elif severity == "MEDIUM":
                action_type = "INVESTIGATE"
            else:
                action_type = "MONITOR"
            
            insight["priority_tier"] = tier
            insight["needs_action"] = needs_action
            insight["action_type"] = action_type
            insight["action_due_date"] = self._calculate_due_date(tier)
        
        return insights
    
    
    def _calculate_due_date(self, tier: str) -> str:
        """Calculate action due date based on tier"""
        from datetime import timedelta
        
        due_days = {
            "IMMEDIATE": 1,
            "HIGH": 2,
            "MEDIUM": 5,
            "LOW": 10,
        }
        
        days = due_days.get(tier, 10)
        due_date = datetime.utcnow() + timedelta(days=days)
        return due_date.isoformat()
    
    
    def get_actions_needed(self, insights: List[Dict]) -> List[Dict]:
        """Get insights that need immediate action"""
        return [i for i in insights if i.get("needs_action", False)]
    
    
    def get_alerts(self, insights: List[Dict]) -> List[Dict]:
        """Get critical alerts"""
        return [i for i in insights if i.get("priority_tier") == "IMMEDIATE"]
    
    
    def group_by_tier(self, insights: List[Dict]) -> Dict[str, List[Dict]]:
        """Group insights by priority tier"""
        tiers = {"IMMEDIATE": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        
        for insight in insights:
            tier = insight.get("priority_tier", "LOW")
            if tier in tiers:
                tiers[tier].append(insight)

        return tiers

    def _normalize_severity(self, severity: str) -> str:
        normalized = str(severity).strip().upper()
        if normalized in {"CRITICAL", "WARNING", "MEDIUM", "INFO"}:
            return normalized
        if normalized in {"HIGH", "CRIT"}:
            return "CRITICAL"
        if normalized in {"WARN"}:
            return "WARNING"
        return "INFO"
