"""
Severity Scoring Module - Module 5
Evaluates and ranks insights by business impact
"""

import logging
from typing import List, Dict, Optional
import numpy as np


class SeverityScorer:
    """
    Scores insights based on:
    1. Intrinsic severity (CRITICAL/WARNING/INFO)
    2. Confidence of detection (rule + ML blend)
    3. Resource criticality
    4. Business impact
    """
    
    SEVERITY_BASE = {"CRITICAL": 100, "WARNING": 50, "INFO": 20}
    RESOURCE_CRITICALITY = {
        "TEMPERATURE": 0.9,
        "MOTOR": 0.95,
        "PRESSURE": 0.8,
        "VIBRATION": 0.85,
        "PUMP": 0.8,
        "SYSTEM": 0.6,
    }
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    
    def score_insights(self, insights: List[Dict]) -> List[Dict]:
        """
        Score all insights and add priority ranking
        
        Args:
            insights: List of insights from insight_orchestrator
        
        Returns:
            Insights with added: priority_score (0-1), priority_rank (1-N)
        """
        
        for insight in insights:
            # Calculate base score from severity
            severity = insight.get("severity", "INFO")
            base_score = self.SEVERITY_BASE.get(severity, 20)
            
            # Factor in confidence (rule + ML)
            rule_conf = insight.get("rule_confidence") or 0.5
            ml_conf = insight.get("ml_confidence") or 0.5
            merged_conf = insight.get("merged_confidence")
            
            if merged_conf is not None:
                confidence_score = merged_conf * 100
            else:
                confidence_score = max(rule_conf, ml_conf) * 100 if (rule_conf or ml_conf) else 50
            
            # Factor in resource criticality
            resource = insight.get("resource", "SYSTEM").upper()
            criticality = self.RESOURCE_CRITICALITY.get(resource, 0.7)
            
            # Calculate final score
            final_score = (
                0.4 * base_score +          # Severity: 40%
                0.35 * confidence_score +   # Confidence: 35%
                0.25 * (criticality * 100)  # Criticality: 25%
            )
            
            # Normalize to 0-1
            priority_score = min(final_score / 100, 1.0)
            
            insight["priority_score"] = priority_score
        
        # Rank by priority
        sorted_insights = sorted(insights, key=lambda x: x["priority_score"], reverse=True)
        
        for rank, insight in enumerate(sorted_insights, 1):
            insight["priority_rank"] = rank
        
        return sorted_insights
    
    
    def get_top_insights(self, insights: List[Dict], top_n: int = 10) -> List[Dict]:
        """Get top N insights by priority"""
        return sorted_insights[:top_n]
    
    
    def categorize_by_severity(self, insights: List[Dict]) -> Dict[str, List[Dict]]:
        """Group insights by severity"""
        categories = {"CRITICAL": [], "WARNING": [], "INFO": []}
        
        for insight in insights:
            severity = insight.get("severity", "INFO")
            if severity in categories:
                categories[severity].append(insight)
        
        return categories
