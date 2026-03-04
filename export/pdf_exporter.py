"""
PDF Exporter — Handles 3 export modes:

MODE 1: Insights-only PDF (A4 portrait, reportlab platypus)
MODE 2: Dashboard-only PDF (A3 landscape, embed base64 PNG)
MODE 4: Full Report PDF (insights A4 + dashboard image pages)

Uses reportlab for all PDF generation. 100% offline.
All table cells use Paragraph objects for proper text wrapping.
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


def _safe_str(val: Any, fallback: str = "") -> str:
    """Safely convert a value to string, escaping XML-bad characters for Paragraph."""
    text = str(val) if val else fallback
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class PDFExporter:
    """
    Multi-mode PDF exporter for Industrial Intelligence reports.
    All text uses Paragraph for proper wrapping — no truncation.
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
        # Cell styles for table content — wrappable
        self.styles.add(ParagraphStyle(
            name="CellNormal",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
        ))
        self.styles.add(ParagraphStyle(
            name="CellBold",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
            fontName="Helvetica-Bold",
        ))
        self.styles.add(ParagraphStyle(
            name="CellHeaderWhite",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=WHITE,
            fontName="Helvetica-Bold",
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
                f"Dashboard Visualization \u2014 Run: {_safe_str(run_id)}",
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
    # MODE 2B — Dashboard PDF from Blueprint (server-side, no screenshot)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def export_dashboard_from_blueprint(
        self,
        run_id: str,
        blueprint: Dict[str, Any],
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Generate a dashboard PDF entirely from the stored blueprint data.
        Used when the frontend cannot capture a screenshot (e.g., Exports page).
        Produces an A4 landscape PDF with KPIs, data table, and insights.
        """
        target_dir = Path(output_dir) if output_dir else EXPORT_DIR / run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(target_dir / f"dashboard_{run_id}_{timestamp}.pdf")

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
        styles = self.styles

        # Title
        story.append(Paragraph(
            f"Dashboard Report &mdash; Run: {_safe_str(run_id)}",
            styles["CoverSubtitle"],
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (server-side)",
            styles["SmallGray"],
        ))
        story.append(Spacer(1, 0.6 * cm))

        sections = blueprint.get("sections", [])
        metadata = blueprint.get("metadata", {})

        # ── KPI Row ──
        kpi_widgets = []
        for sec in sections:
            if sec.get("type") == "kpi_row":
                kpi_widgets = sec.get("widgets", [])
                break

        if kpi_widgets:
            kpi_data = [[
                Paragraph(_safe_str(w.get("title", "")), styles["Normal"])
                for w in kpi_widgets
            ], [
                Paragraph(f"<b>{_safe_str(w.get('value', ''))}</b>", styles["Normal"])
                for w in kpi_widgets
            ]]
            kpi_table = Table(kpi_data, colWidths=[3.5 * cm] * len(kpi_widgets))
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE_HEADER),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GRAY),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.5 * cm))

        # ── Data Tables ──
        for sec in sections:
            if sec.get("type") != "table":
                continue
            for widget in sec.get("widgets", []):
                w_title = widget.get("title", "Data")
                columns = widget.get("columns", [])
                rows = widget.get("data", [])

                if not columns or not rows:
                    continue

                story.append(Paragraph(_safe_str(w_title), styles["Heading3"]))
                story.append(Spacer(1, 0.2 * cm))

                # Build header
                col_keys = [c.get("key", "") for c in columns]
                header = [Paragraph(f"<b>{_safe_str(c.get('label', c.get('key', '')))}</b>",
                                    styles["Normal"]) for c in columns]

                # Build rows (max 50 for PDF readability)
                table_data = [header]
                for row in rows[:50]:
                    table_data.append([
                        Paragraph(_safe_str(row.get(k, "")), styles["Normal"])
                        for k in col_keys
                    ])

                # Calculate column widths
                usable = page_w - 2 * cm
                col_w = usable / max(len(columns), 1)
                t = Table(table_data, colWidths=[col_w] * len(columns))
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.5 * cm))

        # ── Donut/Quality sections as summary text ──
        for sec in sections:
            if sec.get("type") in ("donut_chart", "card"):
                story.append(Paragraph(_safe_str(sec.get("title", "")), styles["Heading3"]))
                for widget in sec.get("widgets", []):
                    title = widget.get("title", "")
                    value = widget.get("value", "")
                    story.append(Paragraph(
                        f"{_safe_str(title)}: <b>{_safe_str(value)}</b>", styles["Normal"]
                    ))
                story.append(Spacer(1, 0.3 * cm))

        if not story or len(story) <= 3:
            story.append(Paragraph("No dashboard data available.", styles["Normal"]))

        doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)
        self.logger.info(f"PDF dashboard (blueprint-based) exported: {filename}")
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
                f"Dashboard \u2014 Run: {_safe_str(run_id)}",
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
        """Build cover page with navy rectangle header block."""
        elements: list = []

        # ── Navy Block as a full-width table ──
        # This renders a navy rectangle with white centered text
        navy_title_style = ParagraphStyle(
            "NavyCoverTitle", parent=self.styles["Title"],
            fontSize=30, textColor=WHITE, alignment=TA_CENTER,
            leading=36, spaceAfter=6,
        )
        navy_subtitle_style = ParagraphStyle(
            "NavyCoverSubtitle", parent=self.styles["Heading2"],
            fontSize=16, textColor=colors.HexColor("#BDD7EE"),
            alignment=TA_CENTER, spaceAfter=4,
        )
        navy_small_style = ParagraphStyle(
            "NavyCoverSmall", parent=self.styles["Normal"],
            fontSize=11, textColor=colors.HexColor("#BDD7EE"),
            alignment=TA_CENTER,
        )

        inner_content = [
            Spacer(1, 2 * cm),
            Paragraph("Industrial Intelligence Report", navy_title_style),
            Spacer(1, 0.3 * cm),
            Paragraph("Offline Analysis &amp; Insights", navy_subtitle_style),
            Spacer(1, 1.2 * cm),
            Paragraph(f"Run ID: {_safe_str(run_id)}", navy_small_style),
            Paragraph(datetime.now().strftime("%B %d, %Y"), navy_small_style),
            Spacer(1, 2 * cm),
        ]

        # Wrap in a single-cell table to get the navy background
        cell_content = []
        for elem in inner_content:
            cell_content.append(elem)

        navy_table_data = [[cell_content]]
        navy_table = Table(navy_table_data, colWidths=[17 * cm])
        navy_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("BOX", (0, 0), (-1, -1), 0, NAVY),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        navy_table.hAlign = "CENTER"

        elements.append(Spacer(1, 3 * cm))
        elements.append(navy_table)
        elements.append(Spacer(1, 1.5 * cm))

        # Confidential badge below navy block
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
            summary_text = _safe_str(narrative["executive_summary"])
        else:
            # Human-readable fallback when no narrative engine ran
            parts = []
            if critical:
                parts.append(
                    f"{critical} issue{'s' if critical > 1 else ''} that need"
                    f"{'s' if critical == 1 else ''} immediate attention"
                )
            if warnings:
                parts.append(
                    f"{warnings} area{'s' if warnings > 1 else ''} worth investigating"
                )
            if info_count:
                parts.append(
                    f"{info_count} informational observation{'s' if info_count > 1 else ''}"
                )
            joined = ", ".join(parts) if parts else "no notable findings"
            summary_text = (
                f"This analysis reviewed the uploaded data and identified "
                f"{joined}. Review the sections below for details and "
                f"recommended actions."
            )

        # Summary box — uses Paragraph for proper text wrapping
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
        sev_display = {
            "CRITICAL": "Needs Immediate Attention",
            "WARNING": "Worth Investigating",
            "INFO": "For Your Information",
        }
        stats_data = [
            [
                Paragraph("Priority Level", self.styles["CellHeaderWhite"]),
                Paragraph("Count", self.styles["CellHeaderWhite"]),
            ],
            [
                Paragraph(sev_display["CRITICAL"], self.styles["CellNormal"]),
                Paragraph(str(critical), self.styles["CellNormal"]),
            ],
            [
                Paragraph(sev_display["WARNING"], self.styles["CellNormal"]),
                Paragraph(str(warnings), self.styles["CellNormal"]),
            ],
            [
                Paragraph(sev_display["INFO"], self.styles["CellNormal"]),
                Paragraph(str(info_count), self.styles["CellNormal"]),
            ],
            [
                Paragraph("<b>Total</b>", self.styles["CellBold"]),
                Paragraph(f"<b>{len(insights)}</b>", self.styles["CellBold"]),
            ],
        ]
        stats_table = Table(stats_data, colWidths=[10 * cm, 4 * cm])
        stats_table.setStyle(self._header_table_style())
        elements.append(stats_table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _data_overview_section(
        self, insights: List[Dict], profiling: Optional[Dict]
    ) -> list:
        """Data overview with profiling stats."""
        elements: list = []

        rows = [
            [
                Paragraph("Metric", self.styles["CellHeaderWhite"]),
                Paragraph("Value", self.styles["CellHeaderWhite"]),
            ]
        ]
        rows.append([
            Paragraph("Total Findings", self.styles["CellNormal"]),
            Paragraph(str(len(insights)), self.styles["CellNormal"]),
        ])
        rows.append([
            Paragraph("Generated", self.styles["CellNormal"]),
            Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), self.styles["CellNormal"]),
        ])

        if profiling:
            cols = profiling.get("columns", {})
            health = profiling.get("quality_metrics", {})
            rows.append([
                Paragraph("Columns Profiled", self.styles["CellNormal"]),
                Paragraph(str(len(cols)), self.styles["CellNormal"]),
            ])
            rows.append([
                Paragraph("Health Score", self.styles["CellNormal"]),
                Paragraph(f"{health.get('health_score', 0):.1f}%", self.styles["CellNormal"]),
            ])

        resources = set(i.get("resource", "N/A") for i in insights)
        rows.append([
            Paragraph("Affected Resources", self.styles["CellNormal"]),
            Paragraph(str(len(resources)), self.styles["CellNormal"]),
        ])

        table = Table(rows, colWidths=[9 * cm, 7 * cm])
        table.setStyle(self._header_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _findings_section(self, insights: List[Dict]) -> list:
        """Key findings table with severity colors.
        ALL text uses Paragraph for proper wrapping — NEVER truncated."""
        elements: list = []
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_insights = sorted(
            insights,
            key=lambda x: severity_order.get(str(x.get("severity", "INFO")).upper(), 3),
        )

        if not sorted_insights:
            elements.append(Paragraph("No findings to report.", self.styles["Normal"]))
            return elements

        sev_display = {
            "CRITICAL": "Needs Attention",
            "WARNING": "Worth Investigating",
            "INFO": "For Info",
        }

        display = sorted_insights[:30]
        header = [
            Paragraph("#", self.styles["CellHeaderWhite"]),
            Paragraph("Priority", self.styles["CellHeaderWhite"]),
            Paragraph("Description", self.styles["CellHeaderWhite"]),
            Paragraph("Confidence", self.styles["CellHeaderWhite"]),
        ]
        rows = [header]

        for i, f in enumerate(display, 1):
            sev = str(f.get("severity", "INFO")).upper()
            # FULL description — NO truncation
            desc = _safe_str(f.get("description", f.get("message", "")))
            conf = f.get("confidence", f.get("priority_score", 0))
            conf_str = f"{float(conf):.0%}" if conf else "N/A"

            # Styled severity label
            sev_label = sev_display.get(sev, sev)
            sev_color = (
                "#DC2626" if sev == "CRITICAL"
                else "#D97306" if sev == "WARNING"
                else "#059669"
            )

            rows.append([
                Paragraph(str(i), self.styles["CellNormal"]),
                Paragraph(
                    f'<font color="{sev_color}"><b>{sev_label}</b></font>',
                    self.styles["CellNormal"],
                ),
                Paragraph(desc, self.styles["CellNormal"]),
                Paragraph(conf_str, self.styles["CellNormal"]),
            ])

        col_widths = [1 * cm, 3 * cm, 10 * cm, 2 * cm]
        table = Table(rows, colWidths=col_widths)
        style_cmds = list(self._header_table_style().getCommands())

        # Color-code severity cells background
        for row_idx in range(1, len(rows)):
            sev_text = str(sorted_insights[row_idx - 1].get("severity", "INFO")).upper()
            if sev_text == "CRITICAL":
                style_cmds.append(("BACKGROUND", (1, row_idx), (1, row_idx), RED_BG))
            elif sev_text == "WARNING":
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
        """Root cause analysis table. ALL text wrapped with Paragraph — no truncation."""
        elements: list = []

        root_causes = []
        for i in insights:
            remediation = i.get("remediation", i.get("action", ""))
            if remediation:
                root_causes.append({
                    "resource": _safe_str(i.get("resource", "N/A")),
                    "finding": _safe_str(i.get("description", i.get("message", ""))),
                    "cause": _safe_str(remediation),
                    "severity": str(i.get("severity", "INFO")).upper(),
                })

        if not root_causes:
            elements.append(Paragraph(
                "No root cause data available.", self.styles["Normal"]
            ))
            return elements

        header = [
            Paragraph("Resource", self.styles["CellHeaderWhite"]),
            Paragraph("Finding", self.styles["CellHeaderWhite"]),
            Paragraph("Recommended Action", self.styles["CellHeaderWhite"]),
            Paragraph("Priority", self.styles["CellHeaderWhite"]),
        ]
        rows = [header]

        sev_display = {
            "CRITICAL": "Needs Attention",
            "WARNING": "Investigate",
            "INFO": "For Info",
        }

        for rc in root_causes[:20]:
            sev = rc["severity"]
            sev_label = sev_display.get(sev, sev)
            sev_color = (
                "#DC2626" if sev == "CRITICAL"
                else "#D97306" if sev == "WARNING"
                else "#059669"
            )

            rows.append([
                Paragraph(rc["resource"], self.styles["CellNormal"]),
                Paragraph(rc["finding"], self.styles["CellNormal"]),
                Paragraph(rc["cause"], self.styles["CellNormal"]),
                Paragraph(
                    f'<font color="{sev_color}"><b>{sev_label}</b></font>',
                    self.styles["CellNormal"],
                ),
            ])

        table = Table(rows, colWidths=[3 * cm, 5 * cm, 6 * cm, 2 * cm])
        table.setStyle(self._header_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _recommendations_section(self, insights: List[Dict]) -> list:
        """3-tier recommendations section. Full sentences — no truncation, no [resource] prefix."""
        elements: list = []

        immediate: list = []
        short_term: list = []
        strategic: list = []

        for i in insights:
            sev = str(i.get("severity", "INFO")).upper()
            action = i.get("remediation", i.get("action", ""))
            if not action:
                desc = i.get("description", i.get("message", ""))
                if desc:
                    action = f"Review and address: {desc}"
                else:
                    continue

            action_str = str(action)
            # Strip "[variable_name]" prefix pattern
            if action_str.startswith("[") and "]" in action_str:
                action_str = action_str[action_str.index("]") + 1:].strip()
                if not action_str:
                    continue

            if sev == "CRITICAL":
                immediate.append(action_str)
            elif sev == "WARNING":
                short_term.append(action_str)
            else:
                strategic.append(action_str)

        tiers = [
            ("Tier 1 \u2014 Immediate Action Required", immediate, RED_TEXT, RED_BG),
            ("Tier 2 \u2014 Investigate This Week", short_term, AMBER_TEXT, AMBER_BG),
            ("Tier 3 \u2014 Strategic Improvement", strategic, BLUE_TEXT, BLUE_BG),
        ]

        for title, items, text_color, bg_color in tiers:
            # Colored header
            header_style = ParagraphStyle(
                f"Tier_{title[:6]}", parent=self.styles["Heading3"],
                textColor=text_color, fontSize=12,
            )
            elements.append(Paragraph(title, header_style))

            if items:
                for item in items[:10]:
                    # FULL text — uses Paragraph for wrapping
                    elements.append(Paragraph(
                        f"\u2022 {_safe_str(item)}",
                        self.styles["Normal"],
                    ))
                if len(items) > 10:
                    elements.append(Paragraph(
                        f"  ... and {len(items) - 10} more",
                        self.styles["SmallGray"],
                    ))
            else:
                elements.append(Paragraph(
                    "No actions required at this level.",
                    self.styles["SmallGray"],
                ))
            elements.append(Spacer(1, 0.3 * cm))

        return elements

    def _predictive_section(self, ml_findings: List[Dict]) -> list:
        """Predictive signals — plain English, no algorithm names."""
        elements: list = []

        if not ml_findings:
            elements.append(Paragraph(
                "No predictive signals generated.", self.styles["Normal"]
            ))
            return elements

        type_labels = {
            "PREDICTION": "Prediction",
            "FORECAST": "Forecast",
            "RISK": "Risk Assessment",
            "ANOMALY": "Anomaly Detection",
        }
        sev_display = {
            "CRITICAL": "Needs Attention",
            "WARNING": "Worth Investigating",
            "INFO": "For Your Information",
        }

        for finding in ml_findings[:10]:
            f_type = finding.get("type", "PREDICTION")
            desc = _safe_str(finding.get("description", ""))
            conf = finding.get("confidence", 0)
            sev = str(finding.get("severity", "INFO")).upper()

            color = RED_TEXT if sev == "CRITICAL" else AMBER_TEXT if sev == "WARNING" else GREEN_TEXT

            type_label = type_labels.get(f_type, f_type)
            sev_label = sev_display.get(sev, sev)

            tag_style = ParagraphStyle(
                f"tag_{f_type}_{id(finding)}", parent=self.styles["Normal"],
                textColor=color, fontSize=10,
            )
            elements.append(Paragraph(
                f"<b>{type_label}:</b> {desc}",
                tag_style,
            ))

            # Confidence in plain English
            conf_val = float(conf) if conf else 0
            if conf_val >= 0.8:
                conf_label = "High confidence"
            elif conf_val >= 0.5:
                conf_label = "Moderate confidence"
            else:
                conf_label = "Low confidence"

            elements.append(Paragraph(
                f"   {conf_label} | {sev_label}",
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
