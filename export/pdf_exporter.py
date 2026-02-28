"""
PDF Exporter — Handles 3 export modes:

MODE 1: Insights-only PDF (A4 portrait, reportlab platypus)
MODE 2: Dashboard-only PDF (A3 landscape, embed base64 PNG)
MODE 4: Full Report PDF (insights A4 + dashboard image pages)

Uses reportlab for all PDF generation. 100% offline.
"""

import base64
import io
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils.paths import EXPORT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────
# Color Palette
# ──────────────────────────────────────────
NAVY = colors.HexColor("#1F4E78")
BLUE_HEADER = colors.HexColor("#366092")
DARK_TEXT = colors.HexColor("#111827")
GRAY_TEXT = colors.HexColor("#6B7280")
RED_BG = colors.HexColor("#FEE2E2")
RED_TEXT = colors.HexColor("#DC2626")
AMBER_BG = colors.HexColor("#FEF3C7")
AMBER_TEXT = colors.HexColor("#D97306")
BLUE_BG = colors.HexColor("#DBEAFE")
BLUE_TEXT = colors.HexColor("#2563EB")
GREEN_TEXT = colors.HexColor("#059669")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
WHITE = colors.white


class PDFExporter:
    """
    Multi-mode PDF exporter for Industrial Intelligence reports.
    """

    def __init__(self) -> None:
        self.logger = logger
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    # ──────────────────────────────────────
    # Custom Styles
    # ──────────────────────────────────────

    def _create_custom_styles(self) -> None:
        """Register custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="CoverTitle",
            parent=self.styles["Title"],
            fontSize=28,
            textColor=NAVY,
            spaceAfter=20,
            alignment=TA_CENTER,
            leading=34,
        ))
        self.styles.add(ParagraphStyle(
            name="CoverSubtitle",
            parent=self.styles["Heading2"],
            fontSize=16,
            textColor=BLUE_HEADER,
            spaceAfter=10,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeading",
            parent=self.styles["Heading1"],
            fontSize=16,
            textColor=NAVY,
            spaceAfter=12,
            spaceBefore=18,
        ))
        self.styles.add(ParagraphStyle(
            name="SubHeading",
            parent=self.styles["Heading2"],
            fontSize=13,
            textColor=BLUE_HEADER,
            spaceAfter=8,
            spaceBefore=12,
        ))
        self.styles.add(ParagraphStyle(
            name="SmallGray",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=GRAY_TEXT,
        ))
        self.styles.add(ParagraphStyle(
            name="FooterStyle",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=GRAY_TEXT,
            alignment=TA_CENTER,
        ))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MODE 1 — Insights-Only PDF
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def export_insights_pdf(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]] = None,
        narrative: Optional[Dict[str, Any]] = None,
        ml_findings: Optional[List[Dict[str, Any]]] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """MODE 1: Generate insights-only PDF (A4 portrait)."""
        target_dir = Path(output_dir) if output_dir else EXPORT_DIR / run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(target_dir / f"insights_report_{run_id}_{timestamp}.pdf")

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2.5 * cm,
        )

        story = self._build_insights_story(
            run_id, unified_insights, profiling_results, narrative, ml_findings
        )

        doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)
        self.logger.info(f"PDF insights report exported: {filename}")
        return filename

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MODE 2 — Dashboard-Only PDF
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def export_dashboard_pdf(
        self,
        run_id: str,
        image_data_base64: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        MODE 2: Generate dashboard screenshot PDF (A3 landscape).

        Parameters
        ----------
        image_data_base64 : str
            Base64-encoded PNG from html2canvas on the frontend.
        """
        target_dir = Path(output_dir) if output_dir else EXPORT_DIR / run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(target_dir / f"dashboard_{run_id}_{timestamp}.pdf")

        # Decode base64 to temp file
        img_bytes = base64.b64decode(image_data_base64)
        tmp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_img.write(img_bytes)
        tmp_img.close()

        try:
            page_w, page_h = landscape(A3)
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(A3),
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=2 * cm,
                bottomMargin=2 * cm,
            )

            story = []

            # Header
            story.append(Paragraph(
                f"Dashboard Visualization — Run: {run_id}",
                self.styles["CoverSubtitle"],
            ))
            story.append(Paragraph(
                f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles["SmallGray"],
            ))
            story.append(Spacer(1, 0.5 * cm))

            # Fit image to page
            usable_w = page_w - 2 * cm
            usable_h = page_h - 5 * cm
            img = Image(tmp_img.name, width=usable_w, height=usable_h)
            img.hAlign = "CENTER"
            story.append(img)

            doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)
            self.logger.info(f"PDF dashboard exported: {filename}")
        finally:
            os.unlink(tmp_img.name)

        return filename

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MODE 4 — Full Report PDF
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def export_full_report_pdf(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        image_data_base64: str,
        profiling_results: Optional[Dict[str, Any]] = None,
        narrative: Optional[Dict[str, Any]] = None,
        ml_findings: Optional[List[Dict[str, Any]]] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        MODE 4: Full report PDF.
        A4 portrait for insights → page break → A3 landscape for dashboard image.

        Uses BaseDocTemplate with two PageTemplates to switch page sizes.
        """
        target_dir = Path(output_dir) if output_dir else EXPORT_DIR / run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(target_dir / f"full_report_{run_id}_{timestamp}.pdf")

        # Decode dashboard image
        img_bytes = base64.b64decode(image_data_base64)
        tmp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_img.write(img_bytes)
        tmp_img.close()

        try:
            # Portrait (A4) frame
            a4_w, a4_h = A4
            portrait_frame = Frame(
                1.5 * cm, 2.5 * cm,
                a4_w - 3 * cm, a4_h - 4.5 * cm,
                id="portrait",
            )
            portrait_tmpl = PageTemplate(
                id="portrait",
                frames=[portrait_frame],
                pagesize=A4,
                onPage=self._add_page_footer,
            )

            # Landscape (A3) frame
            a3_w, a3_h = landscape(A3)
            landscape_frame = Frame(
                1 * cm, 2 * cm,
                a3_w - 2 * cm, a3_h - 4 * cm,
                id="landscape",
            )
            landscape_tmpl = PageTemplate(
                id="landscape",
                frames=[landscape_frame],
                pagesize=landscape(A3),
                onPage=self._add_page_footer,
            )

            doc = BaseDocTemplate(
                filename,
                pageTemplates=[portrait_tmpl, landscape_tmpl],
            )

            story = self._build_insights_story(
                run_id, unified_insights, profiling_results, narrative, ml_findings
            )

            # ── Dashboard Divider Page ──
            story.append(PageBreak())
            story.append(Spacer(1, 6 * cm))
            story.append(Paragraph(
                "Dashboard Visualization",
                self.styles["CoverTitle"],
            ))
            story.append(Paragraph(
                "The following page contains the interactive dashboard snapshot.",
                self.styles["SmallGray"],
            ))

            # Switch to landscape template for dashboard image
            story.append(NextPageTemplate("landscape"))
            story.append(PageBreak())

            # Dashboard image page
            story.append(Paragraph(
                f"Dashboard — Run: {run_id}",
                self.styles["CoverSubtitle"],
            ))
            story.append(Spacer(1, 0.5 * cm))

            usable_w = a3_w - 2 * cm
            usable_h = a3_h - 6 * cm
            img = Image(tmp_img.name, width=usable_w, height=usable_h)
            img.hAlign = "CENTER"
            story.append(img)

            doc.build(story)
            self.logger.info(f"PDF full report exported: {filename}")
        finally:
            os.unlink(tmp_img.name)

        return filename

    # ── Also keep backward-compat method name ──
    def export_comprehensive_report(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """Backward-compatible alias for insights-only PDF."""
        out = output_dir or str(EXPORT_DIR)
        return self.export_insights_pdf(
            run_id=run_id,
            unified_insights=unified_insights,
            profiling_results=profiling_results,
            output_dir=out,
        )

    # ──────────────────────────────────────
    # Story Builders
    # ──────────────────────────────────────

    def _build_insights_story(
        self,
        run_id: str,
        insights: List[Dict[str, Any]],
        profiling: Optional[Dict[str, Any]],
        narrative: Optional[Dict[str, Any]],
        ml_findings: Optional[List[Dict[str, Any]]],
    ) -> list:
        """Build the full insights story (cover → TOC → sections)."""
        story: list = []

        # ── Cover Page ──
        story.extend(self._cover_page(run_id))

        # ── Table of Contents ──
        story.append(Paragraph("Table of Contents", self.styles["SectionHeading"]))
        toc_items = [
            "1. Executive Summary",
            "2. Data Overview",
            "3. Key Findings",
            "4. Root Cause Analysis",
            "5. Recommendations",
            "6. Predictive Signals",
        ]
        for item in toc_items:
            story.append(Paragraph(item, self.styles["Normal"]))
        story.append(PageBreak())

        # ── 1. Executive Summary ──
        story.append(Paragraph("1. Executive Summary", self.styles["SectionHeading"]))
        story.extend(self._executive_summary_section(insights, narrative))

        # ── 2. Data Overview ──
        story.append(Paragraph("2. Data Overview", self.styles["SectionHeading"]))
        story.extend(self._data_overview_section(insights, profiling))

        # ── 3. Key Findings ──
        story.append(PageBreak())
        story.append(Paragraph("3. Key Findings", self.styles["SectionHeading"]))
        story.extend(self._findings_section(insights))

        # ── 4. Root Cause Analysis ──
        story.append(Paragraph("4. Root Cause Analysis", self.styles["SectionHeading"]))
        story.extend(self._root_cause_section(insights))

        # ── 5. Recommendations ──
        story.append(PageBreak())
        story.append(Paragraph("5. Recommendations", self.styles["SectionHeading"]))
        story.extend(self._recommendations_section(insights))

        # ── 6. Predictive Signals ──
        story.append(Paragraph("6. Predictive Signals", self.styles["SectionHeading"]))
        story.extend(self._predictive_section(ml_findings or []))

        return story

    def _cover_page(self, run_id: str) -> list:
        """Build cover page elements."""
        elements: list = []
        elements.append(Spacer(1, 5 * cm))
        elements.append(Paragraph("Industrial Intelligence Report", self.styles["CoverTitle"]))
        elements.append(Paragraph("Offline Analysis & Insights", self.styles["CoverSubtitle"]))
        elements.append(Spacer(1, 2 * cm))
        elements.append(Paragraph(f"Run ID: {run_id}", self.styles["SmallGray"]))
        elements.append(Paragraph(
            datetime.now().strftime("%B %d, %Y"),
            self.styles["SmallGray"],
        ))
        elements.append(Spacer(1, 1 * cm))

        # Confidential badge
        conf_style = ParagraphStyle(
            "ConfBadge", parent=self.styles["Normal"],
            fontSize=10, textColor=RED_TEXT, alignment=TA_CENTER,
        )
        elements.append(Paragraph("<b>CONFIDENTIAL</b>", conf_style))
        elements.append(PageBreak())
        return elements

    def _executive_summary_section(
        self, insights: List[Dict], narrative: Optional[Dict]
    ) -> list:
        """Executive summary with colored summary box."""
        elements: list = []
        critical = sum(1 for i in insights if str(i.get("severity", "")).upper() == "CRITICAL")
        warnings = sum(1 for i in insights if str(i.get("severity", "")).upper() == "WARNING")
        info_count = len(insights) - critical - warnings

        if narrative and narrative.get("executive_summary"):
            summary_text = str(narrative["executive_summary"])
        else:
            summary_text = (
                f"This report contains {len(insights)} findings from automated "
                f"industrial intelligence analysis. "
                f"{critical} critical, {warnings} warnings, {info_count} informational."
            )

        # Summary box
        box_data = [[Paragraph(summary_text, self.styles["Normal"])]]
        box_table = Table(box_data, colWidths=[16 * cm])
        box_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX", (0, 0), (-1, -1), 1, BLUE_HEADER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(box_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Quick stats
        stats_data = [
            ["Metric", "Count"],
            ["Critical", str(critical)],
            ["Warning", str(warnings)],
            ["Info", str(info_count)],
            ["Total", str(len(insights))],
        ]
        stats_table = Table(stats_data, colWidths=[8 * cm, 4 * cm])
        stats_table.setStyle(self._header_table_style())
        elements.append(stats_table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _data_overview_section(
        self, insights: List[Dict], profiling: Optional[Dict]
    ) -> list:
        """Data overview with profiling stats."""
        elements: list = []

        rows = [["Metric", "Value"]]
        rows.append(["Total Findings", str(len(insights))])
        rows.append(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])

        if profiling:
            cols = profiling.get("columns", {})
            health = profiling.get("quality_metrics", {})
            rows.append(["Columns Profiled", str(len(cols))])
            rows.append(["Health Score", f"{health.get('health_score', 0):.1f}%"])

        resources = set(i.get("resource", "N/A") for i in insights)
        rows.append(["Affected Resources", str(len(resources))])

        table = Table(rows, colWidths=[9 * cm, 7 * cm])
        table.setStyle(self._header_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _findings_section(self, insights: List[Dict]) -> list:
        """Key findings table with severity colors."""
        elements: list = []
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_insights = sorted(
            insights,
            key=lambda x: severity_order.get(str(x.get("severity", "INFO")).upper(), 3),
        )

        if not sorted_insights:
            elements.append(Paragraph("No findings to report.", self.styles["Normal"]))
            return elements

        display = sorted_insights[:30]
        header = ["#", "Severity", "Resource", "Description", "Conf."]
        rows = [header]

        for i, f in enumerate(display, 1):
            sev = str(f.get("severity", "INFO")).upper()
            desc = str(f.get("description", f.get("message", "")))[:60]
            conf = f.get("confidence", f.get("priority_score", 0))
            conf_str = f"{float(conf):.0%}" if conf else "N/A"
            rows.append([str(i), sev, str(f.get("resource", ""))[:20], desc, conf_str])

        col_widths = [1 * cm, 2 * cm, 3 * cm, 8 * cm, 2 * cm]
        table = Table(rows, colWidths=col_widths)
        style_cmds = list(self._header_table_style().getCommands())

        # Color-code severity cells
        for row_idx in range(1, len(rows)):
            sev = rows[row_idx][1]
            if sev == "CRITICAL":
                style_cmds.append(("TEXTCOLOR", (1, row_idx), (1, row_idx), RED_TEXT))
                style_cmds.append(("BACKGROUND", (1, row_idx), (1, row_idx), RED_BG))
            elif sev == "WARNING":
                style_cmds.append(("TEXTCOLOR", (1, row_idx), (1, row_idx), AMBER_TEXT))
                style_cmds.append(("BACKGROUND", (1, row_idx), (1, row_idx), AMBER_BG))

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)

        if len(sorted_insights) > 30:
            elements.append(Paragraph(
                f"... and {len(sorted_insights) - 30} additional findings.",
                self.styles["SmallGray"],
            ))
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _root_cause_section(self, insights: List[Dict]) -> list:
        """Root cause analysis table."""
        elements: list = []

        root_causes = []
        for i in insights:
            remediation = i.get("remediation", i.get("action", ""))
            if remediation:
                root_causes.append({
                    "resource": str(i.get("resource", "N/A"))[:20],
                    "finding": str(i.get("description", i.get("message", "")))[:50],
                    "cause": str(remediation)[:60],
                    "severity": str(i.get("severity", "INFO")).upper(),
                })

        if not root_causes:
            elements.append(Paragraph(
                "No root cause data available.", self.styles["Normal"]
            ))
            return elements

        header = ["Resource", "Finding", "Root Cause / Action", "Severity"]
        rows = [header]
        for rc in root_causes[:20]:
            rows.append([rc["resource"], rc["finding"], rc["cause"], rc["severity"]])

        table = Table(rows, colWidths=[3 * cm, 5 * cm, 6 * cm, 2 * cm])
        table.setStyle(self._header_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _recommendations_section(self, insights: List[Dict]) -> list:
        """3-tier recommendations section."""
        elements: list = []

        immediate: list = []
        short_term: list = []
        strategic: list = []

        for i in insights:
            sev = str(i.get("severity", "INFO")).upper()
            action = str(i.get("remediation", i.get("action", i.get("description", ""))))[:100]
            resource = i.get("resource", "")
            entry = f"[{resource}] {action}" if resource else action

            if sev == "CRITICAL":
                immediate.append(entry)
            elif sev == "WARNING":
                short_term.append(entry)
            else:
                strategic.append(entry)

        tiers = [
            ("Tier 1 — Immediate Action", immediate, RED_TEXT, RED_BG),
            ("Tier 2 — Short-Term Investigation", short_term, AMBER_TEXT, AMBER_BG),
            ("Tier 3 — Strategic Improvement", strategic, BLUE_TEXT, BLUE_BG),
        ]

        for title, items, text_color, bg_color in tiers:
            # Colored header
            header_style = ParagraphStyle(
                f"Tier_{title[:6]}", parent=self.styles["Heading3"],
                textColor=text_color, fontSize=12,
            )
            elements.append(Paragraph(title, header_style))

            if items:
                for item in items[:8]:
                    elements.append(Paragraph(f"• {item}", self.styles["Normal"]))
                if len(items) > 8:
                    elements.append(Paragraph(
                        f"  ... and {len(items) - 8} more",
                        self.styles["SmallGray"],
                    ))
            else:
                elements.append(Paragraph(
                    "No recommendations at this tier.",
                    self.styles["SmallGray"],
                ))
            elements.append(Spacer(1, 0.3 * cm))

        return elements

    def _predictive_section(self, ml_findings: List[Dict]) -> list:
        """Predictive signals from ML engine."""
        elements: list = []

        if not ml_findings:
            elements.append(Paragraph(
                "No predictive signals generated.", self.styles["Normal"]
            ))
            return elements

        for finding in ml_findings[:10]:
            f_type = finding.get("type", "PREDICTION")
            desc = finding.get("description", "")
            conf = finding.get("confidence", 0)
            method = finding.get("detection_method", "Unknown")
            sev = str(finding.get("severity", "INFO")).upper()

            color = RED_TEXT if sev == "CRITICAL" else AMBER_TEXT if sev == "WARNING" else GREEN_TEXT

            tag_style = ParagraphStyle(
                f"tag_{f_type}", parent=self.styles["Normal"],
                textColor=color, fontSize=10,
            )
            elements.append(Paragraph(
                f"<b>[{f_type}]</b> {desc}",
                tag_style,
            ))
            elements.append(Paragraph(
                f"   Confidence: {float(conf):.0%} | Method: {method}",
                self.styles["SmallGray"],
            ))
            elements.append(Spacer(1, 0.2 * cm))

        return elements

    # ──────────────────────────────────────
    # Shared Helpers
    # ──────────────────────────────────────

    @staticmethod
    def _header_table_style() -> TableStyle:
        """Standard table style with blue header row."""
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])

    @staticmethod
    def _add_page_footer(canvas, doc) -> None:
        """Draw footer on every page."""
        canvas.saveState()
        date_str = datetime.now().strftime("%B %d, %Y")
        footer_text = f"Confidential | Offline Industrial Intelligence | {date_str}"

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GRAY_TEXT)

        page_w = canvas._pagesize[0]
        canvas.drawCentredString(page_w / 2, 1.2 * cm, footer_text)

        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(page_w - 1.5 * cm, 1.2 * cm, f"Page {page_num}")

        canvas.restoreState()
