"""
Blueprint Generator - Module 6
Generates complete dashboard blueprints from insights and profiles
"""

import logging
from typing import Dict, List, Any, Optional
import uuid
import pandas as pd
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
                 profiling_results: Dict[str, Any],
                 raw_data_sample: Any = None) -> DashboardBlueprint:
        """
        Generate complete dashboard blueprint — DATA-CENTRIC layout.
        
        Layout priority:
          1. KPI Overview Row (compact: rows, columns, health, insights count)
          2. Data Explorer Table (MAIN section — the actual ingested data, ~80%)
          3. Column Profile Summary (compact stats table)
          4. Insights Summary (compact — only top findings, ~10%)
        
        Args:
            run_id: Run identifier
            unified_insights: List from Module 5 orchestration
            profiling_results: From Module 2 profiling
            raw_data_sample: Optional DataFrame with ingested data
        
        Returns:
            DashboardBlueprint ready for frontend
        """
        
        self.logger.info("Generating data-centric dashboard blueprint...")
        
        blueprint = DashboardBlueprint(run_id)
        
        try:
            profiles = profiling_results if isinstance(profiling_results, dict) else {}

            critical_insights = [
                i for i in unified_insights 
                if i.get("severity") == "CRITICAL"
            ]
            warning_insights = [
                i for i in unified_insights
                if i.get("severity") == "WARNING"
            ]

            # ── Row 1: KPI Overview (compact) ───────────────
            kpi_section = self._create_kpi_section(profiles, unified_insights)
            blueprint.sections.append(kpi_section)

            # ── Row 2: DATA EXPLORER TABLE (main section) ───
            if raw_data_sample is not None:
                explorer_section = self._create_data_explorer_section(raw_data_sample)
                if explorer_section:
                    blueprint.sections.append(explorer_section)

            # ── Row 3: Column Profile (compact donut + summary) ─
            donut_section = self._create_donut_chart_section(profiles)
            if donut_section:
                blueprint.sections.append(donut_section)

            # ── Row 4: Data Quality cards (compact) ───────────
            if profiles:
                quality_section = self._create_quality_section(profiles)
                blueprint.sections.append(quality_section)

            # ── Row 5: Insights Summary (compact — top alerts only) ─
            if unified_insights:
                summary_section = self._create_compact_insights_section(unified_insights)
                blueprint.sections.append(summary_section)
            
            # Metadata
            # Calculate data_health from profiles
            _total_cells = 0
            _total_missing = 0
            for _cp in profiles.values():
                if isinstance(_cp, dict):
                    rc = int(_cp.get("total_count", _cp.get("count", 0)))
                    _total_cells += rc
                    _total_missing += int(_cp.get("null_count", 0))
            _data_health = round(100.0 * (1.0 - _total_missing / max(_total_cells, 1)), 1)

            blueprint.metadata = {
                "total_insights": len(unified_insights),
                "critical_count": len(critical_insights),
                "warnings_count": len(warning_insights),
                "data_health": _data_health,
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
        """Create KPI overview cards — data-centric metrics."""

        total_cols = 0
        total_rows_val = 0
        total_missing = 0
        total_cells = 0

        for col_name, col_prof in profiles.items():
            if not isinstance(col_prof, dict):
                continue
            total_cols += 1
            row_count = int(col_prof.get("total_count", col_prof.get("count", col_prof.get("non_null_count", 0))))
            total_rows_val = max(total_rows_val, row_count)
            null_ct = int(col_prof.get("null_count", 0))
            total_missing += null_ct
            total_cells += row_count

        # Data health score = % non-missing cells
        health_pct = round(100.0 * (1.0 - total_missing / max(total_cells, 1)), 1)

        critical_count = len([i for i in insights if i.get("severity") == "CRITICAL"])
        warning_count = len([i for i in insights if i.get("severity") == "WARNING"])

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
                "id": "kpi_critical_count",
                "type": "kpi",
                "title": "Critical Alerts",
                "value": critical_count,
                "icon": "alert",
                "color": "#ef4444" if critical_count > 0 else "#10b981",
            },
            {
                "id": "kpi_warning_count",
                "type": "kpi",
                "title": "Warning Alerts",
                "value": warning_count,
                "icon": "warning",
                "color": "#f59e0b" if warning_count > 0 else "#10b981",
            },
            {
                "id": "kpi_insights_count",
                "type": "kpi",
                "title": "Insights Found",
                "value": len(insights),
                "icon": "lightbulb",
                "color": "#3b82f6",
            },
        ]

        return {
            "id": f"section_kpi_{uuid.uuid4().hex[:8]}",
            "title": "\ud83d\udcca Overview",
            "type": "kpi_row",
            "widgets": widgets,
            "layout": {"columns": len(widgets)},
        }

    # ─────────────────────────────────────────────────────────
    # DATA EXPLORER TABLE — Main section (~80% of dashboard)
    # ─────────────────────────────────────────────────────────

    def _create_data_explorer_section(self, raw_df) -> Optional[Dict[str, Any]]:
        """Create the main Data Explorer table showing the actual ingested data."""
        try:
            if raw_df is None or len(raw_df) == 0:
                return None

            # Determine columns to show (up to 12 most important)
            all_cols = list(raw_df.columns)
            # Filter out internal columns
            skip_prefixes = ("_", "unnamed", "__")
            display_cols = [
                c for c in all_cols
                if not any(str(c).lower().startswith(p) for p in skip_prefixes)
            ]
            # Limit to 12 columns for readability
            display_cols = display_cols[:12]

            if not display_cols:
                return None

            # Build column definitions
            columns = []
            for col in display_cols:
                label = str(col).replace("_", " ").title()
                width = 150
                # Narrower for numeric/short cols, wider for text
                if raw_df[col].dtype in ("float64", "float32", "int64", "int32"):
                    width = 110
                elif raw_df[col].dtype == "object":
                    avg_len = raw_df[col].dropna().astype(str).str.len().mean()
                    width = min(250, max(120, int(avg_len * 8))) if avg_len == avg_len else 150
                columns.append({"key": str(col), "label": label, "width": width})

            # Serialize rows (first 100 for responsiveness)
            sample = raw_df[display_cols].head(100)
            rows = []
            for _, row in sample.iterrows():
                row_dict = {}
                for col in display_cols:
                    val = row[col]
                    if pd.isna(val):
                        row_dict[str(col)] = None
                    elif hasattr(val, "isoformat"):
                        row_dict[str(col)] = val.isoformat()
                    else:
                        row_dict[str(col)] = val
                        # Ensure JSON-safe
                        try:
                            if isinstance(val, float) and (val != val):
                                row_dict[str(col)] = None
                        except Exception:
                            row_dict[str(col)] = str(val)
                rows.append(row_dict)

            widget = {
                "id": "data_explorer_table",
                "type": "table",
                "title": f"Data Explorer \u2014 {len(raw_df)} rows, {len(all_cols)} columns",
                "columns": columns,
                "data": rows,
                "pagination": {"pageSize": 50},
                "total_rows": len(raw_df),
                "total_columns": len(all_cols),
            }

            return {
                "id": f"section_explorer_{uuid.uuid4().hex[:8]}",
                "title": "\ud83d\udcdd Data Explorer",
                "type": "table",
                "widgets": [widget],
                "layout": {"fullWidth": True},
            }
        except Exception as e:
            self.logger.warning(f"Error creating data explorer section: {e}")
            return None

    # ─────────────────────────────────────────────────────────
    # COMPACT INSIGHTS SUMMARY — (~10% of dashboard)
    # ─────────────────────────────────────────────────────────

    def _create_compact_insights_section(self, insights: List[Dict]) -> Dict[str, Any]:
        """Create a compact insights table showing only the top findings."""

        # Take top 10 insights by priority
        top_insights = sorted(
            insights,
            key=lambda i: float(i.get("priority_score", 0.0)),
            reverse=True,
        )[:10]

        widget = {
            "id": "insights_compact_table",
            "type": "table",
            "title": f"Top Findings ({len(top_insights)} of {len(insights)})",
            "columns": [
                {"key": "severity", "label": "Severity", "width": 90},
                {"key": "title", "label": "Finding", "width": 350},
                {"key": "source", "label": "Source", "width": 80},
                {"key": "priority_tier", "label": "Priority", "width": 90},
                {"key": "action_type", "label": "Action", "width": 120},
            ],
            "data": [
                {
                    "severity": i.get("severity", "INFO"),
                    "title": i.get("title", ""),
                    "source": i.get("source", ""),
                    "priority_tier": i.get("priority_tier", ""),
                    "action_type": i.get("action_type", ""),
                }
                for i in top_insights
            ],
            "pagination": {"pageSize": 10},
        }

        return {
            "id": f"section_insights_{uuid.uuid4().hex[:8]}",
            "title": "\ud83d\udca1 Key Findings",
            "type": "table",
            "widgets": [widget],
            "layout": {"fullWidth": True},
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
