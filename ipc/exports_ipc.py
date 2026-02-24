import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from storage.repositories.dashboard_repo import DashboardRepository
from storage.repositories.export_repo import ExportRepository
from storage.repositories.insight_repo import InsightRepository
from storage.repositories.run_repo import RunRepository
from utils.paths import EXPORT_DIR

export_repo = ExportRepository()
run_repo = RunRepository()
insight_repo = InsightRepository()
dashboard_repo = DashboardRepository()


def get_exports_for_run_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "data": None, "message": "Run ID is required"}

    run = run_repo.get_run(run_id)
    if run is None:
        return {"success": False, "data": None, "message": "Run not found"}

    exports = export_repo.get_exports_for_run(run_id)
    return {
        "success": True,
        "data": exports,
        "message": f"Loaded {len(exports)} export records",
    }


def has_exports_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "data": False}

    exists = export_repo.has_exports(run_id)
    return {"success": True, "data": exists}


def generate_export_ipc(
    run_id: str,
    export_type: str,
    scope: str = "both",
    output_dir: str | None = None,
) -> Dict[str, Any]:
    try:
        from export.csv_exporter import CSVExporter
        from export.excel_exporter import ExcelExporter
        from export.pdf_exporter import PDFExporter
    except ModuleNotFoundError as exc:
        return {
            "success": False,
            "data": None,
            "message": (
                f"Missing export dependency: {exc.name}. "
                "Install project requirements before generating exports."
            ),
        }

    if not run_id:
        return {"success": False, "data": None, "message": "Run ID is required"}

    run = run_repo.get_run(run_id)
    if run is None:
        return {"success": False, "data": None, "message": "Run not found"}

    normalized_scope = (scope or "both").strip().lower()
    if normalized_scope not in {"insights", "dashboards", "both"}:
        return {
            "success": False,
            "data": None,
            "message": f"Unsupported scope '{scope}'",
        }

    include_insights = normalized_scope in {"insights", "both"}
    include_dashboards = normalized_scope in {"dashboards", "both"}

    insights = insight_repo.get_insights(run_id) if include_insights else []
    if include_insights and not insights:
        return {
            "success": False,
            "data": None,
            "message": "No insights available to export",
        }

    dashboard_payload = None
    if include_dashboards:
        dashboard_payload = {
            "blueprint": dashboard_repo.get_dashboard_for_run(run_id),
            "user_layout": dashboard_repo.get_user_layout(run_id),
        }
        if not dashboard_payload["blueprint"] and not dashboard_payload["user_layout"]:
            return {
                "success": False,
                "data": None,
                "message": "No dashboard data available to export",
            }

    exported_paths: List[str] = []
    normalized_type = (export_type or "").strip().lower()
    export_kwargs = {}
    if output_dir:
        export_kwargs["output_dir"] = output_dir

    if include_insights:
        if normalized_type == "excel":
            file_path = ExcelExporter().export_full_report(
                run_id=run_id,
                unified_insights=insights,
                profiling_results=None,
                **export_kwargs,
            )
            exported_paths.append(file_path)
            export_repo.save_export(
                export_id=str(uuid.uuid4())[:12],
                run_id=run_id,
                export_type="excel",
                scope=scope,
                file_path=file_path,
            )

        elif normalized_type == "pdf":
            file_path = PDFExporter().export_comprehensive_report(
                run_id=run_id,
                unified_insights=insights,
                profiling_results=None,
                **export_kwargs,
            )
            exported_paths.append(file_path)
            export_repo.save_export(
                export_id=str(uuid.uuid4())[:12],
                run_id=run_id,
                export_type="pdf",
                scope=scope,
                file_path=file_path,
            )

        elif normalized_type == "csv":
            files = CSVExporter().export_batch(
                run_id=run_id,
                unified_insights=insights,
                profiling_results=None,
                **export_kwargs,
            )
            for key, path in files.items():
                exported_paths.append(str(path))
                export_repo.save_export(
                    export_id=str(uuid.uuid4())[:12],
                    run_id=run_id,
                    export_type=key,
                    scope=scope,
                    file_path=str(path),
                )
        else:
            return {
                "success": False,
                "data": None,
                "message": f"Unsupported export_type '{export_type}'",
            }

    if include_dashboards and dashboard_payload is not None:
        target_dir = Path(output_dir) if output_dir else EXPORT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_path = target_dir / f"dashboard_layout_{run_id}_{timestamp}.json"
        with open(dashboard_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "run_id": run_id,
                    "scope": normalized_scope,
                    **dashboard_payload,
                },
                handle,
                indent=2,
                default=str,
            )

        exported_paths.append(str(dashboard_path))
        export_repo.save_export(
            export_id=str(uuid.uuid4())[:12],
            run_id=run_id,
            export_type="dashboard_layout_json",
            scope=scope,
            file_path=str(dashboard_path),
        )

    return {
        "success": True,
        "data": {"paths": exported_paths, "output_dir": output_dir},
        "message": f"Generated {len(exported_paths)} export file(s)",
    }
