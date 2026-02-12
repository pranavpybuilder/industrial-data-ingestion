from typing import Dict, Any
from storage.repositories.export_repo import ExportRepository
from storage.repositories.run_repo import RunRepository

export_repo = ExportRepository()
run_repo = RunRepository()


def get_exports_for_run_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "data": None, "message": "Run ID is required"}

    run = run_repo.get_run(run_id)
    if run is None:
        return {"success": False, "data": None, "message": "Run not found"}

    exports = export_repo.get_exports_for_run(run_id)

    return {"success": True, "data": exports}


def has_exports_ipc(run_id: str) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "data": False}

    exists = export_repo.has_exports(run_id)

    return {"success": True, "data": exists}