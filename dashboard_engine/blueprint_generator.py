"""
Blueprint Generator - Module 6
Generates complete dashboard blueprints from insights and profiles
"""

import logging
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from dashboard_engine.chart_selector import ChartSelector
from dashboard_engine.layout_rules import LayoutRules


class DashboardBlueprint:
    """
    Complete dashboard specification ready for frontend rendering
    """
    
    def __init__(self, run_id: str, blueprint_id: str = None):
        self.run_id = run_id
        self.blueprint_id = blueprint_id or str(uuid.uuid4())[:12]
        self.created_at = datetime.utcnow().isoformat()
        self.sections = []
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the blueprint to a plain dictionary."""
        return {
            "run_id": self.run_id,
            "blueprint_id": self.blueprint_id,
            "created_at": self.created_at,
            "sections": self.sections,
            "metadata": self.metadata,
        }


class BlueprintGenerator:
    """
    Generates dashboard blueprints from unified insights
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.chart_selector = ChartSelector(logger=logger)
        self.layout_rules = LayoutRules(logger=logger)
    
    
    def generate(self,
                 run_id: str,
                 unified_insights: List[Dict],
                 profiling_results: Dict[str, Any]) -> DashboardBlueprint:
        """
        Generate complete dashboard blueprint
        
        Args:
            run_id: Run identifier
            unified_insights: List from Module 5 orchestration
            profiling_results: From Module 2 profiling
        
        Returns:
            DashboardBlueprint ready for frontend
        """
        
        self.logger.info("Generating dashboard blueprint...")
        
        blueprint = DashboardBlueprint(run_id)
        
        try:
            # Section 1: Key Metrics (CRITICAL insights)
            critical_insights = [
                i for i in unified_insights 
                if i.get("severity") == "CRITICAL"
            ]
            
            if critical_insights:
                metrics_section = self._create_metrics_section(critical_insights)
                blueprint.sections.append(metrics_section)
            
            # Section 2: Data Quality (from profiling)
            if profiling_results:
                quality_section = self._create_quality_section(profiling_results)
                blueprint.sections.append(quality_section)
            
            # Section 3: Insights by Resource
            resource_groups = self.layout_rules.group_by_resource(unified_insights)
            
            for resource, insights in resource_groups.items():
                resource_section = self._create_resource_section(resource, insights)
                blueprint.sections.append(resource_section)
            
            # Section 4: All Insights (tabular)
            if unified_insights:
                all_insights_section = self._create_insights_section(unified_insights)
                blueprint.sections.append(all_insights_section)
            
            # Metadata
            blueprint.metadata = {
                "total_insights": len(unified_insights),
                "critical_count": len(critical_insights),
                "warnings_count": len([
                    i for i in unified_insights 
                    if i.get("severity") == "WARNING"
                ]),
                "sections": len(blueprint.sections),
                "generated_at": datetime.utcnow().isoformat(),
            }
            
            self.logger.info(f"Blueprint generated: {len(blueprint.sections)} sections")
            
            return blueprint
        
        except Exception as e:
            self.logger.error(f"Blueprint generation error: {e}", exc_info=True)
            return blueprint
    
    
    def _create_metrics_section(self, insights: List[Dict]) -> Dict[str, Any]:
        """Create critical metrics section"""
        
        widgets = []
        
        for insight in insights[:4]:  # Top 4 critical
            widget = {
                "id": f"metric_{insight.get('insight_id')}",
                "type": "metric",
                "title": insight.get("title", "Critical Alert"),
                "value": insight.get("priority_score", 0),
                "unit": "%",
                "color": "red" if insight.get("severity") == "CRITICAL" else "orange",
                "description": insight.get("description", ""),
                "insight_id": insight.get("insight_id"),
            }
            
            widgets.append(widget)
        
        section = {
            "id": f"section_metrics_{uuid.uuid4().hex[:8]}",
            "title": "🚨 Critical Alerts",
            "type": "metrics",
            "widgets": widgets,
            "layout": self.layout_rules.create_section_layout(
                "Critical Alerts",
                widgets
            ),
        }
        
        return section
    
    
    def _create_quality_section(self, profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Create data quality section"""
        
        widgets = []
        
        for col_name, profile in list(profiles.items())[:6]:
            if not isinstance(profile, dict):
                continue

            null_pct = float(profile.get("null_percentage", 0))
            completeness = max(0.0, 100.0 - null_pct)
            widget = {
                "id": f"quality_{col_name}",
                "type": "card",
                "title": col_name,
                "metrics": {
                    "completeness": round(completeness, 2),
                    "type": profile.get("detected_type", "unknown"),
                    "missing": int(profile.get("null_count", 0)),
                    "outliers": int(profile.get("outlier_count", 0)),
                },
            }

            widgets.append(widget)
        
        section = {
            "id": f"section_quality_{uuid.uuid4().hex[:8]}",
            "title": "📊 Data Quality",
            "type": "quality",
            "widgets": widgets,
            "layout": self.layout_rules.create_section_layout(
                "Data Quality",
                widgets
            ),
        }
        
        return section
    
    
    def _create_resource_section(self, 
                                 resource: str,
                                 insights: List[Dict]) -> Dict[str, Any]:
        """Create section for resource insights"""
        
        widgets = []
        
        for insight in insights[:6]:  # Top 6 per resource
            chart_type = self.chart_selector.select_for_insight(insight)
            
            widget = {
                "id": insight.get("insight_id"),
                "type": chart_type,
                "title": resource,
                "subtitle": insight.get("title", ""),
                "severity": insight.get("severity"),
                "priority": insight.get("priority_tier"),
                "data": {
                    "value": insight.get("priority_score", 0),
                    "description": insight.get("description", ""),
                    "action": insight.get("action_type"),
                },
                "chart_config": self.chart_selector.get_chart_config(chart_type),
            }
            
            widgets.append(widget)
        
        section = {
            "id": f"section_{resource}_{uuid.uuid4().hex[:8]}",
            "title": f"📍 {resource}",
            "type": "resource",
            "widgets": widgets,
            "layout": self.layout_rules.create_section_layout(
                resource,
                widgets
            ),
        }
        
        return section
    
    
    def _create_insights_section(self, insights: List[Dict]) -> Dict[str, Any]:
        """Create full insights table section"""
        
        widget = {
            "id": "insights_table",
            "type": "table",
            "title": "All Insights",
            "columns": [
                {"key": "severity", "label": "Severity", "width": 100},
                {"key": "resource", "label": "Resource", "width": 150},
                {"key": "title", "label": "Title", "width": 300},
                {"key": "source", "label": "Source", "width": 100},
                {"key": "priority_tier", "label": "Priority", "width": 100},
                {"key": "action_type", "label": "Action", "width": 150},
            ],
            "data": [
                {
                    "severity": i.get("severity"),
                    "resource": i.get("resource"),
                    "title": i.get("title"),
                    "source": i.get("source"),
                    "priority_tier": i.get("priority_tier"),
                    "action_type": i.get("action_type"),
                    "insight_id": i.get("insight_id"),
                }
                for i in insights
            ],
            "pagination": {"pageSize": 20},
        }
        
        section = {
            "id": f"section_table_{uuid.uuid4().hex[:8]}",
            "title": "📋 All Insights",
            "type": "table",
            "widgets": [widget],
            "layout": {
                "title": "All Insights",
                "widgets": {
                    "insights_table": {
                        "row": 0,
                        "col": 0,
                        "width": 12,
                        "height": 4,
                    }
                },
                "total_rows": 4,
            },
        }
        
        return section
    
    
    def to_dict(self, blueprint: DashboardBlueprint) -> Dict[str, Any]:
        """Convert blueprint to serializable dict"""
        
        return {
            "blueprint_id": blueprint.blueprint_id,
            "run_id": blueprint.run_id,
            "created_at": blueprint.created_at,
            "sections": blueprint.sections,
            "metadata": blueprint.metadata,
        }
    
    
    def validate_blueprint(self, blueprint: DashboardBlueprint) -> bool:
        """Validate blueprint completeness"""
        
        if not blueprint.sections:
            self.logger.warning("Blueprint has no sections")
            return False
        
        if not blueprint.metadata:
            self.logger.warning("Blueprint missing metadata")
            return False
        
        return True
