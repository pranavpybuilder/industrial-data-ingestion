from typing import Dict, Any, Optional
from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.run_repo import RunRepository
from ingestion.upload_handler import handle_file_upload

ingestion_repo = IngestionRepository()
run_repo = RunRepository()


def upload_file_ipc(
    file_path: str,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    IPC handler: upload and ingest a file.
    Called by the frontend when the user selects a file.
    """
    if not file_path:
        return {
            "success": False,
            "data": None,
            "message": "File path is required",
        }

    result = handle_file_upload(
        file_path=file_path,
        source_type=source_type,
    )

    if not result.get("success"):
        return {
            "success": False,
            "data": None,
            "message": result.get("error", "Ingestion failed"),
        }

    return {
        "success": True,
        "data": result,
        "message": f"Ingested {result['rows']} rows from {result['file_name']}",
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