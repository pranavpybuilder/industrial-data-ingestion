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
            profiles = profiling_results if isinstance(profiling_results, dict) else {}

            # ── Row 1: KPI Overview (always first) ──────────────
            kpi_section = self._create_kpi_section(profiles, unified_insights)
            blueprint.sections.append(kpi_section)

            # ── Row 2: Charts row (bar chart 8-col + donut 4-col) ──
            chart_section = self._create_topn_chart_section(profiles)
            if chart_section:
                blueprint.sections.append(chart_section)

            donut_section = self._create_donut_chart_section(profiles)
            if donut_section:
                blueprint.sections.append(donut_section)

            # ── Row 3: Data Summary Table ──────────────────────
            summary_section = self._create_data_summary_table_section(profiles)
            if summary_section:
                blueprint.sections.append(summary_section)

            # ── Row 4: Data Quality cards (compact) ───────────
            if profiles:
                quality_section = self._create_quality_section(profiles)
                blueprint.sections.append(quality_section)

            # ── Row 5: Critical Alerts (if any) ───────────────
            critical_insights = [
                i for i in unified_insights 
                if i.get("severity") == "CRITICAL"
            ]
            if critical_insights:
                metrics_section = self._create_metrics_section(critical_insights)
                blueprint.sections.append(metrics_section)

            # ── Row 6: All Insights table ─────────────────────
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
    
    
    # ─────────────────────────────────────────────────────────
    # NEW: KPI Overview Section
    # ─────────────────────────────────────────────────────────

    def _create_kpi_section(self, profiles: Dict[str, Any],
                            insights: List[Dict]) -> Dict[str, Any]:
        """Create KPI overview cards with data health score."""

        total_cols = 0
        numeric_cols = 0
        text_cols = 0
        total_rows_val = 0
        total_missing = 0
        total_cells = 0
        top_col_name = "—"
        top_col_mean = 0.0

        for col_name, col_prof in profiles.items():
            if not isinstance(col_prof, dict):
                continue
            total_cols += 1
            row_count = int(col_prof.get("count", col_prof.get("non_null_count", 0)))
            total_rows_val = max(total_rows_val, row_count)
            null_ct = int(col_prof.get("null_count", 0))
            total_missing += null_ct
            total_cells += row_count + null_ct

            dtype = str(col_prof.get("detected_type", "")).lower()
            mean_v = col_prof.get("mean")
            is_numeric = dtype in ("numeric", "float", "int", "integer", "number") or (
                mean_v is not None and isinstance(mean_v, (int, float))
            )
            if is_numeric:
                numeric_cols += 1
                if isinstance(mean_v, (int, float)) and abs(mean_v) > abs(top_col_mean):
                    top_col_mean = mean_v
                    top_col_name = str(col_name).replace("_", " ").title()
            else:
                text_cols += 1

        # Data health score = % non-missing cells
        health_pct = round(100.0 * (1.0 - total_missing / max(total_cells, 1)), 1)

        widgets = [
            {
                "id": "kpi_total_rows",
                "type": "kpi",
                "title": "Total Rows",
                "value": total_rows_val,
                "icon": "rows",
                "color": "#6366f1",
            },
            {
                "id": "kpi_total_columns",
                "type": "kpi",
                "title": "Total Columns",
                "value": total_cols,
                "icon": "columns",
                "color": "#8b5cf6",
            },
            {
                "id": "kpi_data_health",
                "type": "kpi",
                "title": "Data Health",
                "value": f"{health_pct}%",
                "icon": "heart",
                "color": "#10b981" if health_pct >= 90 else "#f59e0b" if health_pct >= 70 else "#ef4444",
            },
            {
                "id": "kpi_missing_values",
                "type": "kpi",
                "title": "Missing Values",
                "value": total_missing,
                "icon": "alert",
                "color": "#ef4444" if total_missing > 0 else "#10b981",
            },
            {
                "id": "kpi_insights_count",
                "type": "kpi",
                "title": "Insights Found",
                "value": len(insights),
                "icon": "lightbulb",
                "color": "#f59e0b",
            },
            {
                "id": "kpi_top_column",
                "type": "kpi",
                "title": "Top Column",
                "value": top_col_name,
                "subtitle": f"avg: {round(top_col_mean, 2)}",
                "icon": "trending_up",
                "color": "#3b82f6",
            },
        ]

        return {
            "id": f"section_kpi_{uuid.uuid4().hex[:8]}",
            "title": "📊 Overview",
            "type": "kpi_row",
            "widgets": widgets,
            "layout": {"columns": len(widgets)},
        }

    # ─────────────────────────────────────────────────────────
    # NEW: Top-N Bar Chart Section
    # ─────────────────────────────────────────────────────────

    def _create_topn_chart_section(self, profiles: Dict[str, Any],
                                   top_n: int = 10) -> Optional[Dict[str, Any]]:
        """Create horizontal bar chart of the top-N numeric columns by mean."""

        entries = []
        for col_name, col_prof in profiles.items():
            if not isinstance(col_prof, dict):
                continue
            mean_v = col_prof.get("mean")
            if mean_v is None or not isinstance(mean_v, (int, float)):
                continue
            entries.append({
                "label": str(col_name).replace("_", " ").title(),
                "column": col_name,
                "value": round(float(mean_v), 2),
            })

        if not entries:
            return None

        # Sort by absolute value descending
        entries.sort(key=lambda e: abs(e["value"]), reverse=True)
        chart_data = entries[:top_n]

        widget = {
            "id": "chart_topn_columns",
            "type": "bar_chart",
            "title": f"Top {len(chart_data)} Columns by Average Value",
            "chart_config": {
                "orientation": "horizontal",
                "color": "#6366f1",
                "showValues": True,
            },
            "data": chart_data,
        }

        return {
            "id": f"section_topn_{uuid.uuid4().hex[:8]}",
            "title": "📈 Top Columns by Average",
            "type": "chart",
            "widgets": [widget],
            "layout": {"fullWidth": True},
        }

    # ─────────────────────────────────────────────────────────
    # NEW: Donut Chart — Column Type Distribution
    # ─────────────────────────────────────────────────────────

    def _create_donut_chart_section(self, profiles: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create donut/pie chart showing column type breakdown."""

        type_counts: Dict[str, int] = {}
        for col_name, col_prof in profiles.items():
            if not isinstance(col_prof, dict):
                continue
            dtype = str(col_prof.get("detected_type", "unknown")).lower()
            mean_v = col_prof.get("mean")
            if dtype in ("numeric", "float", "int", "integer", "number") or (
                mean_v is not None and isinstance(mean_v, (int, float))
            ):
                category = "Numeric"
            elif dtype in ("datetime", "date", "timestamp"):
                category = "Date/Time"
            elif dtype in ("boolean", "bool"):
                category = "Boolean"
            else:
                category = "Text"
            type_counts[category] = type_counts.get(category, 0) + 1

        if not type_counts or len(type_counts) < 1:
            return None

        chart_data = [
            {"label": k, "value": v}
            for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        widget = {
            "id": "chart_column_types",
            "type": "donut_chart",
            "title": "Column Type Distribution",
            "chart_config": {
                "colors": ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"],
                "innerRadius": "60%",
            },
            "data": chart_data,
        }

        return {
            "id": f"section_donut_{uuid.uuid4().hex[:8]}",
            "title": "🍩 Column Types",
            "type": "chart",
            "widgets": [widget],
            "layout": {"gridSpan": 4},
        }

    # ─────────────────────────────────────────────────────────
    # NEW: Data Summary Table Section
    # ─────────────────────────────────────────────────────────

    def _create_data_summary_table_section(self, profiles: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create summary table of all numeric columns with stats."""

        rows = []
        for col_name, col_prof in profiles.items():
            if not isinstance(col_prof, dict):
                continue
            mean_v = col_prof.get("mean")
            if mean_v is None or not isinstance(mean_v, (int, float)):
                continue
            rows.append({
                "column": str(col_name).replace("_", " ").title(),
                "mean": round(float(col_prof.get("mean", 0)), 2),
                "min": round(float(col_prof.get("min", 0)), 2),
                "max": round(float(col_prof.get("max", 0)), 2),
                "std": round(float(col_prof.get("std", 0)), 2),
                "missing": int(col_prof.get("null_count", 0)),
                "missing_pct": round(float(col_prof.get("null_percentage", 0)), 1),
            })

        if not rows:
            return None

        # Sort by mean descending
        rows.sort(key=lambda r: abs(r["mean"]), reverse=True)

        widget = {
            "id": "data_summary_table",
            "type": "table",
            "title": "Numeric Column Summary",
            "columns": [
                {"key": "column", "label": "Column", "width": 220},
                {"key": "mean", "label": "Average", "width": 100},
                {"key": "min", "label": "Min", "width": 80},
                {"key": "max", "label": "Max", "width": 80},
                {"key": "std", "label": "Std Dev", "width": 90},
                {"key": "missing", "label": "Missing", "width": 80},
                {"key": "missing_pct", "label": "Missing %", "width": 80},
            ],
            "data": rows,
            "pagination": {"pageSize": 20},
        }

        return {
            "id": f"section_summary_{uuid.uuid4().hex[:8]}",
            "title": "📋 Data Summary",
            "type": "table",
            "widgets": [widget],
            "layout": {"fullWidth": True},
        }

    # ─────────────────────────────────────────────────────────
    # Existing sections (kept)
    # ─────────────────────────────────────────────────────────

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
