"""
Excel exporter for insights, profiling results, and ML findings.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.worksheet import Worksheet

from utils.paths import EXPORT_DIR


class ExcelExporter:
    """
    Exports insights, profiling results, and ML findings to Excel.
    Multi-sheet workbook with styled headers, auto-fit columns, and formatting.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        )
    
    def export_insights(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export unified insights to Excel workbook.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(out / f"insights_{run_id}_{timestamp}.xlsx")
        
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        
        # Create insights sheet
        self._create_insights_sheet(workbook, unified_insights)
        
        # Create summary sheet
        self._create_summary_sheet(workbook, unified_insights)
        
        workbook.save(filename)
        
        if self.logger:
            self.logger.info(f"Excel insights exported: {filename}")
        
        return filename
    
    def export_profiling(
        self,
        run_id: str,
        profiling_results: Dict[str, Any],
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export profiling results to Excel workbook.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(out / f"profiling_{run_id}_{timestamp}.xlsx")
        
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        
        # Create column profiling sheet
        self._create_column_profiling_sheet(workbook, profiling_results)
        
        # Create data quality sheet
        self._create_data_quality_sheet(workbook, profiling_results)
        
        workbook.save(filename)
        
        if self.logger:
            self.logger.info(f"Excel profiling exported: {filename}")
        
        return filename
    
    def export_full_report(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]] = None,
        output_dir: str = str(EXPORT_DIR),
    ) -> str:
        """
        Export complete report with insights, profiling, and summary.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(out / f"report_{run_id}_{timestamp}.xlsx")
        
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        
        # Create sheets
        self._create_insights_sheet(workbook, unified_insights)
        self._create_summary_sheet(workbook, unified_insights)
        
        if profiling_results:
            self._create_column_profiling_sheet(workbook, profiling_results)
            self._create_data_quality_sheet(workbook, profiling_results)
        
        self._create_metadata_sheet(workbook, run_id, unified_insights, profiling_results)
        
        workbook.save(filename)
        
        if self.logger:
            self.logger.info(f"Excel full report exported: {filename}")
        
        return filename
    
    def _create_insights_sheet(
        self,
        workbook: openpyxl.Workbook,
        insights: List[Dict[str, Any]],
    ):
        """Create detailed insights sheet."""
        ws = workbook.create_sheet("Insights")
        
        headers = [
            "Insight ID",
            "Source",
            "Resource",
            "Severity",
            "Priority Tier",
            "Priority Rank",
            "Priority Score",
            "Chart Type",
            "Action Type",
            "Description",
        ]
        
        self._apply_header_style(ws, headers)
        
        for idx, insight in enumerate(insights, start=2):
            ws[f"A{idx}"] = insight.get("insight_id", "")
            ws[f"B{idx}"] = insight.get("source", "")
            ws[f"C{idx}"] = insight.get("resource", "")
            ws[f"D{idx}"] = insight.get("severity", "")
            ws[f"E{idx}"] = insight.get("priority_tier", "")
            ws[f"F{idx}"] = insight.get("priority_rank", "")
            ws[f"G{idx}"] = round(insight.get("priority_score", 0), 3)
            ws[f"H{idx}"] = insight.get("chart_type", "")
            ws[f"I{idx}"] = insight.get("action_type", "")
            ws[f"J{idx}"] = insight.get("description", "")
            
            for col in range(1, 11):
                cell = ws.cell(row=idx, column=col)
                cell.border = self.thin_border
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        
        # Auto-fit columns
        self._auto_fit_columns(ws, 1, len(insights) + 1, len(headers))
    
    def _create_summary_sheet(
        self,
        workbook: openpyxl.Workbook,
        insights: List[Dict[str, Any]],
    ):
        """Create summary statistics sheet."""
        ws = workbook.create_sheet("Summary")
        
        # Count by severity
        severity_counts = {}
        priority_tier_counts = {}
        action_type_counts = {}
        resource_counts = {}
        
        for insight in insights:
            severity = insight.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            priority_tier = insight.get("priority_tier", "UNKNOWN")
            priority_tier_counts[priority_tier] = priority_tier_counts.get(priority_tier, 0) + 1
            
            action_type = insight.get("action_type", "UNKNOWN")
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
            
            resource = insight.get("resource", "UNKNOWN")
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
        
        row = 1
        
        # Total insights
        ws[f"A{row}"] = "Total Insights"
        ws[f"B{row}"] = len(insights)
        row += 2
        
        # Severity breakdown
        ws[f"A{row}"] = "Severity Breakdown"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1
        
        for severity, count in sorted(severity_counts.items()):
            ws[f"A{row}"] = severity
            ws[f"B{row}"] = count
            
            # Color code severity
            if severity == "CRITICAL":
                fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                ws[f"A{row}"].fill = fill
                ws[f"B{row}"].fill = fill
                ws[f"A{row}"].font = Font(bold=True, color="FFFFFF")
                ws[f"B{row}"].font = Font(bold=True, color="FFFFFF")
            elif severity == "WARNING":
                fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
                ws[f"A{row}"].fill = fill
                ws[f"B{row}"].fill = fill
            
            row += 1
        
        row += 1
        
        # Priority tier breakdown
        ws[f"A{row}"] = "Priority Tier Breakdown"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1
        
        for tier, count in sorted(priority_tier_counts.items()):
            ws[f"A{row}"] = tier
            ws[f"B{row}"] = count
            row += 1
        
        row += 1
        
        # Resource breakdown
        ws[f"A{row}"] = "Resource Breakdown"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1
        
        for resource, count in sorted(resource_counts.items()):
            ws[f"A{row}"] = resource
            ws[f"B{row}"] = count
            row += 1
        
        # Auto-fit columns
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 15
    
    def _create_column_profiling_sheet(
        self,
        workbook: openpyxl.Workbook,
        profiling_results: Dict[str, Any],
    ):
        """Create column profiling details sheet."""
        ws = workbook.create_sheet("Column Profiling")
        
        columns = profiling_results.get("columns", {})
        
        headers = [
            "Column Name",
            "Type",
            "Non-Null %",
            "Unique Values",
            "Missing Count",
            "Mean",
            "Median",
            "Std Dev",
            "Min",
            "Max",
        ]
        
        self._apply_header_style(ws, headers)
        
        row = 2
        for col_name, col_info in columns.items():
            ws[f"A{row}"] = col_name
            ws[f"B{row}"] = col_info.get("type", "")
            ws[f"C{row}"] = f"{col_info.get('non_null_percentage', 0):.1f}%"
            ws[f"D{row}"] = col_info.get("unique_values", 0)
            ws[f"E{row}"] = col_info.get("missing_count", 0)
            ws[f"F{row}"] = round(col_info.get("mean", 0), 4) if col_info.get("mean") else ""
            ws[f"G{row}"] = round(col_info.get("median", 0), 4) if col_info.get("median") else ""
            ws[f"H{row}"] = round(col_info.get("std_dev", 0), 4) if col_info.get("std_dev") else ""
            ws[f"I{row}"] = col_info.get("min", "")
            ws[f"J{row}"] = col_info.get("max", "")
            
            for col in range(1, 11):
                ws.cell(row=row, column=col).border = self.thin_border
            
            row += 1
        
        # Auto-fit columns
        self._auto_fit_columns(ws, 1, len(columns) + 1, len(headers))
    
    def _create_data_quality_sheet(
        self,
        workbook: openpyxl.Workbook,
        profiling_results: Dict[str, Any],
    ):
        """Create data quality assessment sheet."""
        ws = workbook.create_sheet("Data Quality")
        
        quality = profiling_results.get("quality_metrics", {})
        
        health_score = quality.get("health_score", 0)
        
        ws["A1"] = "Data Quality Assessment"
        ws["A1"].font = Font(bold=True, size=14)
        
        row = 3
        
        ws[f"A{row}"] = "Health Score"
        ws[f"B{row}"] = f"{health_score:.1f}%"
        
        # Color code health score
        if health_score >= 80:
            fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")
        elif health_score >= 60:
            fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        else:
            fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        
        ws[f"B{row}"].fill = fill
        ws[f"B{row}"].font = Font(bold=True)
        
        row += 2
        
        # Issues
        issues = quality.get("issues", [])
        
        if issues:
            ws[f"A{row}"] = "Data Issues"
            ws[f"A{row}"].font = Font(bold=True)
            row += 1
            
            for issue in issues:
                ws[f"A{row}"] = issue.get("column", "")
                ws[f"B{row}"] = issue.get("issue_type", "")
                ws[f"C{row}"] = issue.get("severity", "")
                row += 1
        
        # Auto-fit columns
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 15
    
    def _create_metadata_sheet(
        self,
        workbook: openpyxl.Workbook,
        run_id: str,
        insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]],
    ):
        """Create metadata sheet with export information."""
        ws = workbook.create_sheet("Metadata")
        
        row = 1
        
        ws[f"A{row}"] = "Run ID"
        ws[f"B{row}"] = run_id
        row += 1
        
        ws[f"A{row}"] = "Export Date"
        ws[f"B{row}"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row += 1
        
        ws[f"A{row}"] = "Total Insights"
        ws[f"B{row}"] = len(insights)
        row += 1
        
        if profiling_results:
            ws[f"A{row}"] = "Total Columns"
            ws[f"B{row}"] = len(profiling_results.get("columns", {}))
            row += 1
        
        # Auto-fit columns
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 40
    
    def _apply_header_style(self, ws: Worksheet, headers: List[str]):
        """Apply header styling to worksheet."""
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.thin_border
    
    def _auto_fit_columns(
        self,
        ws: Worksheet,
        min_row: int,
        max_row: int,
        num_columns: int,
    ):
        """Auto-fit column widths based on content."""
        for col in range(1, num_columns + 1):
            max_length = 0
            column = openpyxl.utils.get_column_letter(col)
            
            for row in range(min_row, max_row + 1):
                cell = ws[f"{column}{row}"]
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
