"""
Equipment Analyzer - Post-profiling statistical intelligence
Generates business-level insights from equipment data
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import logging


class EquipmentAnalyzer:
    """
    Analyzes equipment data to generate business insights:
    - Equipment failure frequency
    - Downtime statistics
    - Failure type distribution
    - Root cause patterns
    - Technician workload
    - Spare replacement patterns
    - Equipment risk scoring
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze equipment data and generate insights
        
        Expected columns:
        - equipment_id or Equipment ID
        - breakdown_count or Breakdown Count
        - downtime or Downtime (hours)
        - failure_type or Failure Type
        - root_cause or Root Cause
        - technician or Technician
        - spare_part or Part Replaced / Spare Part
        - severity or Duration
        
        Returns: Equipment intelligence report
        """
        
        self.logger.info("Starting Equipment Analysis")
        
        # Normalize column names
        df = self._normalize_columns(df)
        
        insights = {}
        
        # 1. Equipment failure frequency
        insights["equipment_frequency"] = self._analyze_equipment_frequency(df)
        
        # 2. Downtime analysis
        insights["downtime_analysis"] = self._analyze_downtime(df)
        
        # 3. Failure type distribution
        insights["failure_types"] = self._analyze_failure_types(df)
        
        # 4. Root cause patterns
        insights["root_causes"] = self._analyze_root_causes(df)
        
        # 5. Technician workload
        insights["technician_load"] = self._analyze_technician_load(df)
        
        # 6. Spare replacement patterns
        insights["spare_patterns"] = self._analyze_spare_patterns(df)
        
        # 7. Equipment risk scoring
        insights["equipment_risk"] = self._score_equipment_risk(
            df,
            insights["equipment_frequency"],
            insights["downtime_analysis"],
        )
        
        # 8. Data quality assessment
        insights["data_quality"] = self._assess_data_quality(df)
        
        # 9. Anomalies and alerts
        insights["alerts"] = self._generate_alerts(
            df,
            insights["downtime_analysis"],
            insights["root_causes"],
            insights["spare_patterns"],
        )
        
        self.logger.info(f"Equipment Analysis Complete")
        
        return insights
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format"""
        df = df.copy()
        
        column_map = {
            "Equipment ID": "equipment_id",
            "Equipment": "equipment_id",
            "Equipment_ID": "equipment_id",
            "Breakdown Count": "breakdown_count",
            "Breakdown_Count": "breakdown_count",
            "Count": "breakdown_count",
            "Downtime": "downtime_hours",
            "Downtime (hrs)": "downtime_hours",
            "Duration": "downtime_hours",
            "Failure Type": "failure_type",
            "Failure_Type": "failure_type",
            "Type": "failure_type",
            "Root Cause": "root_cause",
            "Root_Cause": "root_cause",
            "Cause": "root_cause",
            "Technician": "technician",
            "Technician ID": "technician",
            "Tech": "technician",
            "Spare Part": "spare_part",
            "Spare_Part": "spare_part",
            "Part Replaced": "spare_part",
            "Part": "spare_part",
            "Severity": "severity",
            "5-Why": "five_why_depth",
            "5_Why": "five_why_depth",
        }
        
        for old_col, new_col in column_map.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        return df
    
    def _analyze_equipment_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze breakdown frequency per equipment"""
        
        # Get breakdown counts (by count column or by grouped records)
        if "breakdown_count" in df.columns:
            freq_data = df.groupby("equipment_id")["breakdown_count"].sum().sort_values(ascending=False)
        else:
            # Group by equipment_id and count records
            freq_data = df.groupby("equipment_id").size().sort_values(ascending=False)
        
        total_breakdowns = freq_data.sum()
        unique_equipment = len(freq_data)
        
        # Top equipment
        top_3 = freq_data.head(3)
        
        return {
            "total_breakdowns": int(total_breakdowns),
            "total_equipment": int(unique_equipment),
            "top_failing_equipment": [
                {
                    "equipment_id": str(eq_id),
                    "breakdown_count": int(count),
                    "percentage": round(count / total_breakdowns * 100, 1),
                    "risk_level": self._get_risk_level_frequency(count, total_breakdowns),
                }
                for eq_id, count in top_3.items()
            ],
            "frequency_distribution": {
                str(k): int(v) for k, v in freq_data.to_dict().items()
            }
        }
    
    def _analyze_downtime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze downtime statistics"""
        
        if "downtime_hours" not in df.columns:
            return {"total_downtime": 0, "average_downtime": 0}
        
        downtime_col = pd.to_numeric(df["downtime_hours"], errors='coerce')
        downtime_col = downtime_col.dropna()
        
        if len(downtime_col) == 0:
            return {"total_downtime": 0, "average_downtime": 0}
        
        total_downtime = downtime_col.sum()
        avg_downtime = downtime_col.mean()
        max_downtime = downtime_col.max()
        min_downtime = downtime_col.min()
        
        # Equipment-specific downtime
        equipment_downtime = {}
        if "equipment_id" in df.columns:
            for eq_id in df["equipment_id"].unique():
                eq_data = downtime_col[df["equipment_id"] == eq_id]
                if len(eq_data) > 0:
                    equipment_downtime[str(eq_id)] = {
                        "total_hours": round(eq_data.sum(), 1),
                        "average_hours": round(eq_data.mean(), 2),
                        "max_hours": round(eq_data.max(), 1),
                        "count": int(len(eq_data)),
                    }
        
        # Anomalies: downtime > 12 hours
        extreme_downtime = downtime_col[downtime_col > 12]
        
        return {
            "total_downtime_hours": round(total_downtime, 1),
            "average_downtime_hours": round(avg_downtime, 2),
            "max_downtime_hours": round(max_downtime, 1),
            "min_downtime_hours": round(min_downtime, 1),
            "extreme_events_count": int(len(extreme_downtime)),
            "extreme_threshold_hours": 12,
            "equipment_downtime": equipment_downtime,
        }
    
    def _analyze_failure_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failure type distribution"""
        
        if "failure_type" not in df.columns:
            return {}
        
        type_counts = df["failure_type"].value_counts()
        total = type_counts.sum()
        
        return {
            "total_failures": int(total),
            "failure_types": [
                {
                    "type": str(ftype),
                    "count": int(count),
                    "percentage": round(count / total * 100, 1),
                }
                for ftype, count in type_counts.items()
            ],
            "dominant_type": str(type_counts.index[0]) if len(type_counts) > 0 else None,
        }
    
    def _analyze_root_causes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze root cause patterns"""
        
        if "root_cause" not in df.columns:
            return {}
        
        cause_counts = df["root_cause"].value_counts()
        total = cause_counts.sum()
        
        return {
            "total_identified_causes": int(total),
            "root_causes": [
                {
                    "cause": str(cause),
                    "count": int(count),
                    "percentage": round(count / total * 100, 1),
                }
                for cause, count in cause_counts.items()
            ],
            "top_causes": [str(c) for c in cause_counts.head(5).index.tolist()],
        }
    
    def _analyze_technician_load(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze technician workload distribution"""
        
        if "technician" not in df.columns:
            return {}
        
        tech_counts = df["technician"].value_counts()
        total = tech_counts.sum()
        avg_load = total / len(tech_counts) if len(tech_counts) > 0 else 0
        
        return {
            "total_technicians": int(len(tech_counts)),
            "total_breakdowns_assigned": int(total),
            "average_load_per_technician": round(avg_load, 1),
            "technician_load": [
                {
                    "technician": str(tech),
                    "breakdown_count": int(count),
                    "percentage": round(count / total * 100, 1),
                    "load_status": "High" if count > avg_load * 1.2 else "Normal",
                }
                for tech, count in tech_counts.items()
            ],
        }
    
    def _analyze_spare_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spare part replacement patterns"""
        
        if "spare_part" not in df.columns:
            return {}
        
        spare_counts = df["spare_part"].value_counts()
        total = spare_counts.sum()
        
        # Detect repeat failures (same spare in 30 days)
        repeat_failures = []
        if "equipment_id" in df.columns:
            for spare in spare_counts.index:
                spare_records = df[df["spare_part"] == spare]
                if len(spare_records) > 1:
                    repeat_failures.append({
                        "spare": str(spare),
                        "replacement_count": spare_counts[spare],
                        "risk_indicator": "High" if spare_counts[spare] >= 3 else "Medium",
                    })
        
        return {
            "total_replacements": int(total),
            "unique_spares": int(len(spare_counts)),
            "most_replaced": [
                {
                    "part": str(part),
                    "replaced_count": int(count),
                    "percentage": round(count / total * 100, 1),
                }
                for part, count in spare_counts.head(10).items()
            ],
            "repeat_failure_alerts": repeat_failures,
        }
    
    def _score_equipment_risk(
        self,
        df: pd.DataFrame,
        freq_analysis: Dict,
        downtime_analysis: Dict,
    ) -> Dict[str, Any]:
        """Generate equipment risk scores"""
        
        equipment_risk = []
        
        for eq_dict in freq_analysis.get("top_failing_equipment", []):
            eq_id = eq_dict["equipment_id"]
            
            # Risk factors
            frequency_score = eq_dict.get("breakdown_count", 0) / max(1, freq_analysis.get("total_breakdowns", 1))
            
            eq_downtime = downtime_analysis.get("equipment_downtime", {}).get(eq_id, {})
            downtime_score = eq_downtime.get("average_hours", 0) / max(1, downtime_analysis.get("average_downtime_hours", 1))
            
            # Combined risk score
            risk_score = (frequency_score * 0.6 + min(downtime_score, 1.0) * 0.4)
            
            equipment_risk.append({
                "equipment_id": eq_id,
                "risk_score": round(risk_score, 3),
                "risk_category": "HIGH" if risk_score >= 0.7 else "MEDIUM" if risk_score >= 0.4 else "LOW",
                "frequency_factor": round(frequency_score, 3),
                "downtime_factor": round(min(downtime_score, 1.0), 3),
                "recommendation": self._get_risk_recommendation(eq_id, eq_dict, eq_downtime),
            })
        
        return {
            "equipment_risk_scores": equipment_risk,
            "high_risk_count": sum(1 for r in equipment_risk if r["risk_category"] == "HIGH"),
        }
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess documentation and data quality"""
        
        quality_issues = []
        
        # Check for incomplete 5-why documentation
        if "five_why_depth" in df.columns:
            incomplete = df[pd.to_numeric(df["five_why_depth"], errors='coerce') < 3]
            if len(incomplete) > 0:
                incompleteness_pct = round(len(incomplete) / len(df) * 100, 1)
                quality_issues.append({
                    "issue_type": "Incomplete 5-Why Documentation",
                    "affected_records": int(len(incomplete)),
                    "percentage": incompleteness_pct,
                    "severity": "High" if incompleteness_pct > 20 else "Medium",
                })
        
        # Check for missing root causes
        if "root_cause" in df.columns:
            missing_causes = df["root_cause"].isna().sum()
            if missing_causes > 0:
                missing_pct = round(missing_causes / len(df) * 100, 1)
                quality_issues.append({
                    "issue_type": "Missing Root Cause",
                    "affected_records": int(missing_causes),
                    "percentage": missing_pct,
                    "severity": "High" if missing_pct > 15 else "Medium",
                })
        
        return {
            "total_records_analyzed": int(len(df)),
            "completeness_score": max(0, 100 - sum(i.get("percentage", 0) for i in quality_issues)),
            "quality_issues": quality_issues,
        }
    
    def _generate_alerts(
        self,
        df: pd.DataFrame,
        downtime_analysis: Dict,
        root_causes: Dict,
        spare_patterns: Dict,
    ) -> List[Dict[str, Any]]:
        """Generate actionable alerts from analysis"""
        
        alerts = []
        
        # Alert: Extreme downtime events
        if downtime_analysis.get("extreme_events_count", 0) > 0:
            alerts.append({
                "alert_type": "Extreme Downtime Events",
                "severity": "HIGH",
                "count": downtime_analysis["extreme_events_count"],
                "description": f"{downtime_analysis['extreme_events_count']} records exceeded 12-hour threshold",
                "action": "Investigate root causes of extended downtime",
            })
        
        # Alert: Repeat spare failures
        if spare_patterns.get("repeat_failure_alerts"):
            alerts.append({
                "alert_type": "Repeat Spare Failures",
                "severity": "HIGH",
                "count": len(spare_patterns.get("repeat_failure_alerts", [])),
                "description": "Multiple spare parts replaced within 30 days",
                "action": "Recommend preventive maintenance for affected equipment",
            })
        
        # Alert: Data quality
        quality_issues = self._assess_data_quality(df).get("quality_issues", [])
        if quality_issues:
            alerts.append({
                "alert_type": "Data Quality Issues",
                "severity": "MEDIUM",
                "count": len(quality_issues),
                "description": f"{len(quality_issues)} documentation issues identified",
                "action": "Improve 5-Why and root cause documentation",
            })
        
        return alerts
    
    def _get_risk_level_frequency(self, count: int, total: int) -> str:
        """Get risk level based on frequency"""
        percentage = (count / total * 100) if total > 0 else 0
        if percentage > 10:
            return "High"
        elif percentage > 5:
            return "Medium"
        return "Low"
    
    def _get_risk_recommendation(
        self,
        eq_id: str,
        freq_dict: Dict,
        downtime_dict: Dict,
    ) -> str:
        """Get specific risk recommendation"""
        
        breakdown_count = freq_dict.get("breakdown_count", 0)
        avg_downtime = downtime_dict.get("average_hours", 0)
        
        if breakdown_count > 15 or avg_downtime > 6:
            return "Implement scheduled inspection and preventive maintenance"
        elif breakdown_count > 10:
            return "Increase monitoring frequency and plan maintenance"
        else:
            return "Monitor performance and schedule routine checks"
