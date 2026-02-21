"""
PDF exporter for insights and profiling reports.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


class PDFExporter:
    """
    Exports insights and profiling results to PDF reports.
    Multi-page PDF with table of contents, charts, and formatted tables.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for PDF."""
        self.styles.add(ParagraphStyle(
            name="CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1F4E78"),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=self.styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#366092"),
            spaceAfter=12,
            spaceBefore=12,
        ))
        
        self.styles.add(ParagraphStyle(
            name="CustomNormal",
            parent=self.styles["Normal"],
            fontSize=11,
            leading=14,
        ))
    
    def export_insights_report(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        output_dir: str = "data/exports",
    ) -> str:
        """
        Export insights to PDF report.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/insights_report_{run_id}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"Insights Report - {run_id}", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3*inch))
        
        # Export timestamp
        export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {export_date}", self.styles["Normal"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary statistics
        story.append(Paragraph("Summary Statistics", self.styles["SectionTitle"]))
        story.extend(self._create_summary_tables(unified_insights))
        story.append(Spacer(1, 0.2*inch))
        
        # Detailed insights table
        story.append(PageBreak())
        story.append(Paragraph("Detailed Insights", self.styles["SectionTitle"]))
        story.extend(self._create_insights_tables(unified_insights))
        
        doc.build(story)
        
        if self.logger:
            self.logger.info(f"PDF insights report exported: {filename}")
        
        return filename
    
    def export_profiling_report(
        self,
        run_id: str,
        profiling_results: Dict[str, Any],
        output_dir: str = "data/exports",
    ) -> str:
        """
        Export profiling results to PDF report.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/profiling_report_{run_id}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"Data Profiling Report - {run_id}", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3*inch))
        
        # Export timestamp
        export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {export_date}", self.styles["Normal"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Data quality overview
        story.append(Paragraph("Data Quality Overview", self.styles["SectionTitle"]))
        story.extend(self._create_quality_overview(profiling_results))
        story.append(Spacer(1, 0.2*inch))
        
        # Column profiling
        story.append(Paragraph("Column Profiling", self.styles["SectionTitle"]))
        story.extend(self._create_column_tables(profiling_results))
        
        # Issues (if any)
        quality = profiling_results.get("quality_metrics", {})
        issues = quality.get("issues", [])
        
        if issues:
            story.append(PageBreak())
            story.append(Paragraph("Data Quality Issues", self.styles["SectionTitle"]))
            story.extend(self._create_issues_table(issues))
        
        doc.build(story)
        
        if self.logger:
            self.logger.info(f"PDF profiling report exported: {filename}")
        
        return filename
    
    def export_comprehensive_report(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]] = None,
        output_dir: str = "data/exports",
    ) -> str:
        """
        Export comprehensive report with insights and profiling.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/comprehensive_report_{run_id}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"Comprehensive Intelligence Report - {run_id}", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3*inch))
        
        # Export timestamp
        export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {export_date}", self.styles["Normal"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Insights summary
        story.append(Paragraph("Insights Summary", self.styles["SectionTitle"]))
        story.extend(self._create_summary_tables(unified_insights))
        story.append(Spacer(1, 0.2*inch))
        
        # Detailed insights
        story.append(PageBreak())
        story.append(Paragraph("Detailed Insights", self.styles["SectionTitle"]))
        story.extend(self._create_insights_tables(unified_insights))
        
        # Data quality (if available)
        if profiling_results:
            story.append(PageBreak())
            story.append(Paragraph("Data Quality Assessment", self.styles["SectionTitle"]))
            story.extend(self._create_quality_overview(profiling_results))
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph("Column Profiling", self.styles["SectionTitle"]))
            story.extend(self._create_column_tables(profiling_results))
            
            quality = profiling_results.get("quality_metrics", {})
            issues = quality.get("issues", [])
            
            if issues:
                story.append(PageBreak())
                story.append(Paragraph("Data Quality Issues", self.styles["SectionTitle"]))
                story.extend(self._create_issues_table(issues))
        
        doc.build(story)
        
        if self.logger:
            self.logger.info(f"PDF comprehensive report exported: {filename}")
        
        return filename
    
    def _create_summary_tables(self, insights: List[Dict[str, Any]]) -> List:
        """Create summary statistics tables."""
        elements = []
        
        # Count by severity
        severity_counts = {}
        priority_tier_counts = {}
        
        for insight in insights:
            severity = insight.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            priority_tier = insight.get("priority_tier", "UNKNOWN")
            priority_tier_counts[priority_tier] = priority_tier_counts.get(priority_tier, 0) + 1
        
        # Severity table
        severity_data = [["Severity", "Count"]]
        for severity in sorted(severity_counts.keys()):
            severity_data.append([severity, str(severity_counts[severity])])
        
        severity_table = Table(severity_data, colWidths=[3*inch, 1*inch])
        severity_table.setStyle(self._get_table_style())
        elements.append(severity_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Priority tier table
        priority_data = [["Priority Tier", "Count"]]
        for tier in sorted(priority_tier_counts.keys()):
            priority_data.append([tier, str(priority_tier_counts[tier])])
        
        priority_table = Table(priority_data, colWidths=[3*inch, 1*inch])
        priority_table.setStyle(self._get_table_style())
        elements.append(priority_table)
        
        return elements
    
    def _create_insights_tables(self, insights: List[Dict[str, Any]]) -> List:
        """Create detailed insights tables."""
        elements = []
        
        # Batch insights into multiple tables (max 20 rows per table)
        batch_size = 20
        
        for batch_idx in range(0, len(insights), batch_size):
            batch = insights[batch_idx:batch_idx + batch_size]
            
            table_data = [[
                "ID",
                "Source",
                "Resource",
                "Severity",
                "Priority",
                "Score",
                "Action",
            ]]
            
            for insight in batch:
                table_data.append([
                    insight.get("insight_id", "")[:20],
                    insight.get("source", ""),
                    insight.get("resource", ""),
                    insight.get("severity", ""),
                    insight.get("priority_tier", "")[:8],
                    f"{insight.get('priority_score', 0):.2f}",
                    insight.get("action_type", ""),
                ])
            
            table = Table(table_data, colWidths=[0.8*inch, 0.8*inch, 1*inch, 0.9*inch, 0.8*inch, 0.6*inch, 1.3*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_quality_overview(self, profiling_results: Dict[str, Any]) -> List:
        """Create data quality overview section."""
        elements = []
        
        quality = profiling_results.get("quality_metrics", {})
        health_score = quality.get("health_score", 0)
        
        overview_data = [
            ["Metric", "Value"],
            ["Health Score", f"{health_score:.1f}%"],
            ["Total Columns", str(len(profiling_results.get("columns", {})))],
            ["Missing Values", str(quality.get("total_missing", 0))],
        ]
        
        overview_table = Table(overview_data, colWidths=[2.5*inch, 2.5*inch])
        overview_table.setStyle(self._get_table_style())
        elements.append(overview_table)
        
        return elements
    
    def _create_column_tables(self, profiling_results: Dict[str, Any]) -> List:
        """Create column profiling tables."""
        elements = []
        
        columns = profiling_results.get("columns", {})
        batch_size = 15
        
        col_list = list(columns.items())
        
        for batch_idx in range(0, len(col_list), batch_size):
            batch = col_list[batch_idx:batch_idx + batch_size]
            
            table_data = [[
                "Column",
                "Type",
                "Non-Null %",
                "Unique",
                "Mean",
            ]]
            
            for col_name, col_info in batch:
                table_data.append([
                    col_name[:20],
                    col_info.get("type", ""),
                    f"{col_info.get('non_null_percentage', 0):.1f}%",
                    str(col_info.get("unique_values", 0)),
                    f"{col_info.get('mean', 0):.2f}" if col_info.get("mean") else "N/A",
                ])
            
            table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_issues_table(self, issues: List[Dict[str, Any]]) -> List:
        """Create data quality issues table."""
        elements = []
        
        table_data = [[
            "Column",
            "Issue Type",
            "Severity",
            "Details",
        ]]
        
        for issue in issues:
            table_data.append([
                issue.get("column", ""),
                issue.get("issue_type", ""),
                issue.get("severity", ""),
                issue.get("details", "")[:50],
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        table.setStyle(self._get_table_style())
        elements.append(table)
        
        return elements
    
    def _get_table_style(self) -> TableStyle:
        """Get standard table styling."""
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGNMENT", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
