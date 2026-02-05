from typing import Dict, Any
from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.run_repo import RunRepository

ingestion_repo = IngestionRepository()
run_repo = RunRepository()


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