from typing import Any, Dict, Optional

from app.pipeline_runner import PipelineRunner
from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.run_repo import RunRepository

ingestion_repo = IngestionRepository()
run_repo = RunRepository()
pipeline_runner = PipelineRunner()

SOURCE_TYPE_MAP = {
    "SAP": "sap",
    "RFID": "rfid",
    "PLC": "plc",
    "EXCEL": "generic_tabular",
    "ENERGY": "energy",
    "REPORT_EXCEL": "report_excel",
    "OPERATIONAL_EXCEL": "operational_excel",
}


def _normalize_source_type(source_type: Optional[str]) -> Optional[str]:
    if not source_type:
        return None

    cleaned = source_type.strip()
    if cleaned in SOURCE_TYPE_MAP:
        return SOURCE_TYPE_MAP[cleaned]

    lowered = cleaned.lower()
    if lowered in SOURCE_TYPE_MAP.values():
        return lowered

    return cleaned


def upload_file_ipc(
    file_path: str,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    IPC handler: run full ingestion pipeline for a file.
    """
    if not file_path:
        return {
            "success": False,
            "data": None,
            "message": "File path is required",
        }

    normalized_source = _normalize_source_type(source_type)
    result = pipeline_runner.run_single_file(
        file_path=file_path,
        source_type=normalized_source,
    )

    if not result.get("success"):
        step = result.get("failed_step", "unknown")
        return {
            "success": False,
            "data": result,
            "message": f"Pipeline failed at '{step}': {result.get('error')}",
        }

    return {
        "success": True,
        "data": result,
        "message": (
            f"Run {result['run_id']} completed successfully. "
            f"Ingested {result['rows']} rows."
        ),
    }


def get_ingestion_status_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {
            "success": False,
            "data": None,
            "message": "Run ID is required",
        }

    run = run_repo.get_run(run_id)
    if run is None:
        return {
            "success": False,
            "data": None,
            "message": "Run not found",
        }

    files = ingestion_repo.get_ingested_files(run_id)

    return {
        "success": True,
        "data": {
            "run_id": run_id,
            "status": run.get("status"),
            "has_ingestion": len(files) > 0,
            "files": files,
        },
    }


def reset_ingestion_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "message": "Run ID is required"}

    run = run_repo.get_run(run_id)
    if run is None:
        return {"success": False, "message": "Run not found"}

    ingestion_repo.delete_ingestion_for_run(run_id)

    return {"success": True, "message": "Ingestion data reset successfully"}
