"""
Export IPC Handlers — All 7 export endpoints.

Handlers:
1. exportInsightsDocx(runId)         → MODE 1 DOCX
2. exportInsightsPdf(runId)          → MODE 1 PDF
3. exportDashboardPdf(runId, base64) → MODE 2 PDF
4. exportDashboardJson(runId)        → MODE 3 JSON
5. exportFullReport(runId, base64)   → MODE 4 PDF
6. openExportFile(filePath)          → OS open
7. getExportHistory(runId)           → export records

All return: {success: bool, data?: dict, message?: str, error?: str}
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage.repositories.dashboard_repo import DashboardRepository
from storage.repositories.export_repo import ExportRepository
from storage.repositories.insight_repo import InsightRepository
from storage.repositories.run_repo import RunRepository
from utils.paths import EXPORT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

export_repo = ExportRepository()
run_repo = RunRepository()
insight_repo = InsightRepository()
dashboard_repo = DashboardRepository()


def _get_run_export_dir(run_id: str) -> Path:
    """Get the export directory for a specific run."""
    run_dir = EXPORT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _save_export_record(
    run_id: str,
    export_type: str,
    scope: str,
    file_path: str,
) -> None:
    """Persist an export record to the database."""
    export_repo.save_export(
        export_id=str(uuid.uuid4())[:12],
        run_id=run_id,
        export_type=export_type,
        scope=scope,
        file_path=file_path,
    )


def _load_insights_and_profiling(run_id: str):
    """Load insights and profiling data for a run, with validation."""
    run = run_repo.get_run(run_id)
    if run is None:
        return None, None, "Run not found"

    insights = insight_repo.get_insights(run_id)

    # Profiling is optional — don't fail if missing.
    # The DB stores profiling as a flat list of column records;
    # exporters expect {columns: {col_name: {...}}, quality_metrics: {...}}.
    profiling = None
    try:
        from storage.repositories.profiling_repo import ProfilingRepository
        profiling_repo = ProfilingRepository()
        raw_rows = profiling_repo.get_profiling_results(run_id)
        if raw_rows:
            columns: dict = {}
            total_missing = 0
            issues: list = []
            for row in raw_rows:
                col_name = row.get("column_name", "unknown")
                miss_pct = float(row.get("missing_percentage", 0))
                columns[col_name] = {
                    "type": row.get("detected_type", "unknown"),
                    "non_null_percentage": max(0.0, 100.0 - miss_pct),
                    "missing_percentage": miss_pct,
                    "missing_count": 0,
                    "unique_values": 0,
                    "distinct_count": 0,
                    "outlier_count": int(row.get("outlier_count", 0)),
                }
                if miss_pct > 5:
                    issues.append({
                        "column": col_name,
                        "issue_type": f"{miss_pct:.1f}% missing",
                        "severity": "warning" if miss_pct < 30 else "critical",
                        "details": f"{col_name} has {miss_pct:.1f}% missing values",
                    })
                total_missing += int(row.get("outlier_count", 0))
            profiling = {
                "columns": columns,
                "quality_metrics": {
                    "health_score": 0.0,
                    "total_missing": total_missing,
                    "issues": issues,
                },
            }
    except Exception:
        profiling = None

    return insights, profiling, None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. exportInsightsDocx(runId)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def export_insights_docx_ipc(run_id: str, output_dir: str = "") -> Dict[str, Any]:
    """MODE 1 — Generate insights DOCX report."""
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    try:
        from export.docx_exporter import DocxExporter

        insights, profiling, err = _load_insights_and_profiling(run_id)
        if err:
            return {"success": False, "message": err}
        if not insights:
            return {"success": False, "message": "No insights available for this run"}

        output_dir = output_dir if output_dir else str(_get_run_export_dir(run_id))
        exporter = DocxExporter()
        file_path = exporter.export_insights_docx(
            run_id=run_id,
            unified_insights=insights,
            profiling_results=profiling,
            output_dir=output_dir,
        )

        _save_export_record(run_id, "insights_docx", "insights", file_path)
        logger.info(f"DOCX export completed: {file_path}")

        return {
            "success": True,
            "data": {"file_path": file_path},
            "message": "DOCX insights report generated successfully",
        }

    except ImportError as exc:
        return {
            "success": False,
            "message": f"Missing dependency for DOCX export: {exc.name}. Install python-docx.",
            "error": str(exc),
        }
    except Exception as exc:
        logger.error(f"DOCX export failed: {exc}")
        return {"success": False, "message": f"DOCX export failed: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. exportInsightsPdf(runId)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def export_insights_pdf_ipc(run_id: str, output_dir: str = "") -> Dict[str, Any]:
    """MODE 1 — Generate insights PDF report (A4 portrait)."""
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    try:
        from export.pdf_exporter import PDFExporter

        insights, profiling, err = _load_insights_and_profiling(run_id)
        if err:
            return {"success": False, "message": err}
        if not insights:
            return {"success": False, "message": "No insights available for this run"}

        output_dir = output_dir if output_dir else str(_get_run_export_dir(run_id))
        exporter = PDFExporter()
        file_path = exporter.export_insights_pdf(
            run_id=run_id,
            unified_insights=insights,
            profiling_results=profiling,
            output_dir=output_dir,
        )

        _save_export_record(run_id, "insights_pdf", "insights", file_path)
        logger.info(f"PDF insights export completed: {file_path}")

        return {
            "success": True,
            "data": {"file_path": file_path},
            "message": "PDF insights report generated successfully",
        }

    except ImportError as exc:
        return {
            "success": False,
            "message": f"Missing dependency for PDF export: {exc.name}. Install reportlab.",
            "error": str(exc),
        }
    except Exception as exc:
        logger.error(f"PDF insights export failed: {exc}")
        return {"success": False, "message": f"PDF export failed: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. exportDashboardPdf(runId, imageDataBase64)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def export_dashboard_pdf_ipc(run_id: str, image_data_base64: str, output_dir: str = "") -> Dict[str, Any]:
    """MODE 2 — Generate dashboard PDF.
    If image_data_base64 is provided, embeds the screenshot (A3 landscape).
    If empty, generates a data-centric PDF from the stored blueprint.
    """
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    try:
        from export.pdf_exporter import PDFExporter

        output_dir = output_dir if output_dir else str(_get_run_export_dir(run_id))
        exporter = PDFExporter()

        if image_data_base64:
            # Strip data URI prefix if present
            if "," in image_data_base64:
                image_data_base64 = image_data_base64.split(",", 1)[1]

            file_path = exporter.export_dashboard_pdf(
                run_id=run_id,
                image_data_base64=image_data_base64,
                output_dir=output_dir,
            )
        else:
            # Server-side fallback: generate PDF from blueprint data
            from storage.repositories.dashboard_repo import DashboardRepository
            dashboard_repo = DashboardRepository()
            dashboard = dashboard_repo.get_dashboard_for_run(run_id)
            if not dashboard:
                return {"success": False, "message": "No dashboard found for this run. Process the file first."}

            file_path = exporter.export_dashboard_from_blueprint(
                run_id=run_id,
                blueprint=dashboard,
                output_dir=output_dir,
            )

        _save_export_record(run_id, "dashboard_pdf", "dashboard", file_path)
        logger.info(f"Dashboard PDF export completed: {file_path}")

        return {
            "success": True,
            "data": {"file_path": file_path},
            "message": "Dashboard PDF generated successfully",
        }

    except Exception as exc:
        logger.error(f"Dashboard PDF export failed: {exc}")
        return {"success": False, "message": f"Dashboard PDF export failed: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. exportDashboardJson(runId)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def export_dashboard_json_ipc(run_id: str, output_dir: str = "") -> Dict[str, Any]:
    """MODE 3 — Export dashboard blueprint + user layout as JSON."""
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    try:
        blueprint = dashboard_repo.get_dashboard_for_run(run_id)
        user_layout = dashboard_repo.get_user_layout(run_id)

        if not blueprint and not user_layout:
            return {"success": False, "message": "No dashboard data available for this run"}

        resolved_dir = Path(output_dir) if output_dir else _get_run_export_dir(run_id)
        resolved_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(resolved_dir / f"dashboard_layout_{run_id}_{timestamp}.json")

        payload = {
            "format_version": "1.0",
            "export_type": "dashboard_blueprint",
            "run_id": run_id,
            "exported_at": datetime.now().isoformat(),
            "blueprint": blueprint,
            "user_layout": user_layout,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        _save_export_record(run_id, "dashboard_json", "dashboard", filename)
        logger.info(f"Dashboard JSON export completed: {filename}")

        return {
            "success": True,
            "data": {"file_path": filename},
            "message": "Dashboard JSON exported successfully",
        }

    except Exception as exc:
        logger.error(f"Dashboard JSON export failed: {exc}")
        return {"success": False, "message": f"Dashboard JSON export failed: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. exportFullReport(runId, imageDataBase64)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def export_full_report_ipc(run_id: str, image_data_base64: str, output_dir: str = "") -> Dict[str, Any]:
    """MODE 4 — Generate full report PDF (insights A4 + dashboard A3)."""
    if not run_id:
        return {"success": False, "message": "Run ID is required"}
    if not image_data_base64:
        return {"success": False, "message": "Dashboard image data is required"}

    try:
        from export.pdf_exporter import PDFExporter

        # Strip data URI prefix if present
        if "," in image_data_base64:
            image_data_base64 = image_data_base64.split(",", 1)[1]

        insights, profiling, err = _load_insights_and_profiling(run_id)
        if err:
            return {"success": False, "message": err}
        if not insights:
            return {"success": False, "message": "No insights available for this run"}

        output_dir = output_dir if output_dir else str(_get_run_export_dir(run_id))
        exporter = PDFExporter()
        file_path = exporter.export_full_report_pdf(
            run_id=run_id,
            unified_insights=insights,
            image_data_base64=image_data_base64,
            profiling_results=profiling,
            output_dir=output_dir,
        )

        _save_export_record(run_id, "full_report_pdf", "full", file_path)
        logger.info(f"Full report PDF export completed: {file_path}")

        return {
            "success": True,
            "data": {"file_path": file_path},
            "message": "Full report PDF generated successfully",
        }

    except Exception as exc:
        logger.error(f"Full report export failed: {exc}")
        return {"success": False, "message": f"Full report export failed: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. openExportFile(filePath)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def open_export_file_ipc(file_path: str) -> Dict[str, Any]:
    """Open an exported file in the OS default application."""
    if not file_path:
        return {"success": False, "message": "File path is required"}

    path = Path(file_path)
    if not path.exists():
        return {"success": False, "message": f"File not found: {file_path}"}

    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

        return {
            "success": True,
            "data": {"file_path": str(path)},
            "message": "File opened successfully",
        }
    except Exception as exc:
        logger.error(f"Failed to open file: {exc}")
        return {"success": False, "message": f"Failed to open file: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. getExportHistory(runId)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_export_history_ipc(run_id: str) -> Dict[str, Any]:
    """Get export history for a run."""
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    try:
        run = run_repo.get_run(run_id)
        if run is None:
            return {"success": False, "message": "Run not found"}

        exports = export_repo.get_exports_for_run(run_id)

        # Enrich with file existence check
        for export_record in exports:
            fp = export_record.get("file_path", "")
            export_record["file_exists"] = Path(fp).exists() if fp else False

        return {
            "success": True,
            "data": {"exports": exports},
            "message": f"Loaded {len(exports)} export records",
        }

    except Exception as exc:
        logger.error(f"Failed to get export history: {exc}")
        return {"success": False, "message": f"Failed to get export history: {exc}", "error": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Backward-compatible aliases
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_exports_for_run_ipc(run_id: str) -> Dict[str, Any]:
    """Legacy alias for getExportHistory."""
    return get_export_history_ipc(run_id)


def has_exports_ipc(run_id: str) -> Dict[str, Any]:
    """Check if a run has any exports."""
    if not run_id:
        return {"success": False, "data": False}
    exists = export_repo.has_exports(run_id)
    return {"success": True, "data": exists}


def generate_export_ipc(
    run_id: str,
    export_type: str,
    scope: str = "both",
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Legacy multi-purpose export handler.
    Routes to the appropriate new handler based on export_type.
    """
    normalized = (export_type or "").strip().lower()

    if normalized == "pdf":
        return export_insights_pdf_ipc(run_id)
    elif normalized == "docx":
        return export_insights_docx_ipc(run_id)
    elif normalized == "excel":
        try:
            from export.excel_exporter import ExcelExporter
            insights, profiling, err = _load_insights_and_profiling(run_id)
            if err:
                return {"success": False, "message": err}
            if not insights:
                return {"success": False, "message": "No insights available"}

            out = output_dir or str(_get_run_export_dir(run_id))
            file_path = ExcelExporter().export_full_report(
                run_id=run_id,
                unified_insights=insights,
                profiling_results=profiling,
                output_dir=out,
            )
            _save_export_record(run_id, "excel", scope, file_path)
            return {
                "success": True,
                "data": {"file_path": file_path},
                "message": "Excel report generated successfully",
            }
        except Exception as exc:
            return {"success": False, "message": str(exc), "error": str(exc)}

    return {"success": False, "message": f"Unsupported export type: {export_type}"}

