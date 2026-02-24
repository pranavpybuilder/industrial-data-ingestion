"""
CSV exporter for insights and profiling data.
"""
import os
import csv
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.paths import EXPORT_DIR


class CSVExporter:
    """
    Exports insights and profiling results to CSV files.
    Supports batch export of multiple related CSV files.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def export_insights(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export unified insights to CSV file.
        One row per insight with all attributes.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/insights_{run_id}_{timestamp}.csv"
        
        if not unified_insights:
            if self.logger:
                self.logger.warning("No insights to export")
            return filename
        
        # Get all unique keys from insights
        fieldnames = set()
        for insight in unified_insights:
            fieldnames.update(insight.keys())
        fieldnames = sorted(list(fieldnames))
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unified_insights)
        
        if self.logger:
            self.logger.info(f"CSV insights exported: {filename}")
        
        return filename
    
    def export_insights_summary(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export insights summary statistics to CSV.
        One row per summary metric.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/insights_summary_{run_id}_{timestamp}.csv"
        
        summary_data = []
        
        # Total insights
        summary_data.append({
            "metric": "Total Insights",
            "value": len(unified_insights),
        })
        
        # Count by severity
        severity_counts = {}
        for insight in unified_insights:
            severity = insight.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity in sorted(severity_counts.keys()):
            summary_data.append({
                "metric": f"Severity: {severity}",
                "value": severity_counts[severity],
            })
        
        # Count by priority tier
        priority_counts = {}
        for insight in unified_insights:
            priority = insight.get("priority_tier", "UNKNOWN")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority in sorted(priority_counts.keys()):
            summary_data.append({
                "metric": f"Priority: {priority}",
                "value": priority_counts[priority],
            })
        
        # Count by resource
        resource_counts = {}
        for insight in unified_insights:
            resource = insight.get("resource", "UNKNOWN")
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
        
        for resource in sorted(resource_counts.keys()):
            summary_data.append({
                "metric": f"Resource: {resource}",
                "value": resource_counts[resource],
            })
        
        # Count by action type
        action_counts = {}
        for insight in unified_insights:
            action = insight.get("action_type", "UNKNOWN")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action in sorted(action_counts.keys()):
            summary_data.append({
                "metric": f"Action: {action}",
                "value": action_counts[action],
            })
        
        # Average priority score
        if unified_insights:
            avg_score = sum(
                insight.get("priority_score", 0) for insight in unified_insights
            ) / len(unified_insights)
            summary_data.append({
                "metric": "Average Priority Score",
                "value": f"{avg_score:.3f}",
            })
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["metric", "value"])
            writer.writeheader()
            writer.writerows(summary_data)
        
        if self.logger:
            self.logger.info(f"CSV insights summary exported: {filename}")
        
        return filename
    
    def export_profiling(
        self,
        run_id: str,
        profiling_results: Dict[str, Any],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export column profiling results to CSV file.
        One row per column with statistics.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/profiling_{run_id}_{timestamp}.csv"
        
        columns = profiling_results.get("columns", {})
        
        if not columns:
            if self.logger:
                self.logger.warning("No profiling data to export")
            return filename
        
        rows = []
        for col_name, col_info in columns.items():
            rows.append({
                "column_name": col_name,
                "type": col_info.get("type", ""),
                "non_null_percentage": f"{col_info.get('non_null_percentage', 0):.1f}%",
                "unique_values": col_info.get("unique_values", 0),
                "missing_count": col_info.get("missing_count", 0),
                "missing_percentage": f"{col_info.get('missing_percentage', 0):.1f}%",
                "mean": f"{col_info.get('mean', 0):.4f}" if col_info.get("mean") is not None else "",
                "median": f"{col_info.get('median', 0):.4f}" if col_info.get("median") is not None else "",
                "std_dev": f"{col_info.get('std_dev', 0):.4f}" if col_info.get("std_dev") is not None else "",
                "min": col_info.get("min", ""),
                "max": col_info.get("max", ""),
                "distinct_count": col_info.get("distinct_count", 0),
            })
        
        fieldnames = [
            "column_name",
            "type",
            "non_null_percentage",
            "unique_values",
            "missing_count",
            "missing_percentage",
            "mean",
            "median",
            "std_dev",
            "min",
            "max",
            "distinct_count",
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        if self.logger:
            self.logger.info(f"CSV profiling exported: {filename}")
        
        return filename
    
    def export_data_quality(
        self,
        run_id: str,
        profiling_results: Dict[str, Any],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export data quality metrics and issues to CSV.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/data_quality_{run_id}_{timestamp}.csv"
        
        quality = profiling_results.get("quality_metrics", {})
        issues = quality.get("issues", [])
        
        rows = []
        
        # Health score
        rows.append({
            "category": "Overall",
            "type": "Health Score",
            "column": "N/A",
            "severity": "N/A",
            "value": f"{quality.get('health_score', 0):.1f}%",
            "details": "",
        })
        
        # Issues
        for issue in issues:
            rows.append({
                "category": "Issue",
                "type": issue.get("issue_type", ""),
                "column": issue.get("column", ""),
                "severity": issue.get("severity", ""),
                "value": "",
                "details": issue.get("details", ""),
            })
        
        fieldnames = [
            "category",
            "type",
            "column",
            "severity",
            "value",
            "details",
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        if self.logger:
            self.logger.info(f"CSV data quality exported: {filename}")
        
        return filename
    
    def export_batch(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]] = None,
        output_dir: str = str(EXPORT_DIR),
    ) -> Dict[str, str]:
        """
        Export all insights and profiling data to batch of CSV files.
        Returns dict mapping file type to filename.
        """
        results = {
            "insights": self.export_insights(run_id, unified_insights, output_dir),
            "insights_summary": self.export_insights_summary(run_id, unified_insights, output_dir),
        }
        
        if profiling_results:
            results["profiling"] = self.export_profiling(run_id, profiling_results, output_dir)
            results["data_quality"] = self.export_data_quality(run_id, profiling_results, output_dir)
        
        if self.logger:
            self.logger.info(f"Batch CSV export complete: {len(results)} files")
        
        return results
