"""
Chart Selector - Module 6
Intelligently selects chart types based on data characteristics
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum


class ChartType(str, Enum):
    """Available chart types"""
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    COLUMN = "column"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    DONUT = "donut"
    GAUGE = "gauge"
    METRIC = "metric"
    TABLE = "table"
    HEATMAP = "heatmap"
    SANKEY = "sankey"
    TREE = "tree"


class ChartSelector:
    """
    Selects optimal chart type based on data characteristics
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    
    def select_chart_type(self, 
                         feature_name: str,
                         feature_type: str,
                         unique_values: int,
                         is_temporal: bool,
                         is_numeric: bool,
                         cardinality_ratio: float) -> str:
        """
        Select chart type for a feature
        
        Args:
            feature_name: Name of feature
            feature_type: Type (numeric, categorical, temporal, etc.)
            unique_values: Count of unique values
            is_temporal: Is time-series data
            is_numeric: Is numeric data
            cardinality_ratio: unique_values / total_rows
        
        Returns:
            Recommended chart type
        """
        
        # Temporal numeric data
        if is_temporal and is_numeric:
            if cardinality_ratio > 0.1:
                return ChartType.SCATTER
            else:
                return ChartType.LINE
        
        # Temporal categorical
        if is_temporal and not is_numeric:
            return ChartType.BAR
        
        # High cardinality numeric (>30 unique)
        if is_numeric and unique_values > 30:
            return ChartType.HISTOGRAM
        
        # Low cardinality numeric (<=30 unique)
        if is_numeric and unique_values <= 30:
            return ChartType.COLUMN
        
        # Categorical with high cardinality (>10)
        if not is_numeric and unique_values > 10:
            return ChartType.TABLE
        
        # Categorical with low cardinality (<=10)
        if not is_numeric and unique_values <= 10:
            if unique_values <= 5:
                return ChartType.PIE
            else:
                return ChartType.BAR
        
        # Single value (metric/KPI)
        if unique_values == 1:
            return ChartType.METRIC
        
        return ChartType.TABLE
    
    
    def select_for_insight(self, insight: Dict) -> str:
        """
        Select chart for unified insight
        
        Args:
            insight: From orchestration layer
                {source, severity, resource, feature_name, priority_score, ...}
        
        Returns:
            Chart type for this insight
        """
        
        priority = insight.get("priority_score", 0.5)
        severity = insight.get("severity", "INFO")
        
        # Critical insights → Metric/Gauge for prominence
        if severity == "CRITICAL":
            return ChartType.GAUGE
        
        # High priority insights → Bar or Column
        if priority > 0.7:
            return ChartType.COLUMN
        
        # Default for insights → Card/Metric
        return ChartType.METRIC
    
    
    def select_for_correlation(self) -> str:
        """Select chart for correlation matrix"""
        return ChartType.HEATMAP
    
    
    def select_for_distribution(self) -> str:
        """Select chart for distribution analysis"""
        return ChartType.HISTOGRAM
    
    
    def select_for_hierarchy(self) -> str:
        """Select chart for hierarchical data"""
        return ChartType.TREE
    
    
    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """
        Get default configuration for chart type
        
        Returns:
            Configuration dict with series, axes, legend, tooltip settings
        """
        
        configs = {
            ChartType.LINE: {
                "type": "line",
                "series": {"smooth": True, "tension": 0.4},
                "xaxis": {"type": "category"},
                "yaxis": {"type": "value"},
                "legend": {"show": True, "position": "bottom"},
                "tooltip": {"show": True},
            },
            ChartType.AREA: {
                "type": "area",
                "series": {"smooth": True},
                "xaxis": {"type": "category"},
                "yaxis": {"type": "value"},
                "legend": {"show": True},
            },
            ChartType.BAR: {
                "type": "bar",
                "direction": "horizontal",
                "xaxis": {"type": "value"},
                "yaxis": {"type": "category"},
                "legend": {"show": True},
            },
            ChartType.COLUMN: {
                "type": "column",
                "direction": "vertical",
                "xaxis": {"type": "category"},
                "yaxis": {"type": "value"},
                "legend": {"show": False},
            },
            ChartType.SCATTER: {
                "type": "scatter",
                "xaxis": {"type": "value"},
                "yaxis": {"type": "value"},
                "legend": {"show": True},
            },
            ChartType.HISTOGRAM: {
                "type": "histogram",
                "xaxis": {"type": "value"},
                "yaxis": {"type": "value"},
                "legend": {"show": False},
            },
            ChartType.PIE: {
                "type": "pie",
                "legend": {"show": True, "position": "right"},
                "tooltip": {"show": True},
            },
            ChartType.DONUT: {
                "type": "donut",
                "legend": {"show": True},
            },
            ChartType.GAUGE: {
                "type": "gauge",
                "min": 0,
                "max": 100,
                "progress": {"show": True},
            },
            ChartType.METRIC: {
                "type": "metric",
                "fontSize": "32px",
                "fontWeight": "bold",
            },
            ChartType.TABLE: {
                "type": "table",
                "pagination": {"pageSize": 10},
            },
            ChartType.HEATMAP: {
                "type": "heatmap",
                "colorScale": "sequential",
            },
        }
        
        return configs.get(chart_type, {})
