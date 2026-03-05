from storage.repositories.run_repo import RunRepository
from storage.connection import get_run_file_name

run_repo = RunRepository()


def get_active_run_ipc():
    run = run_repo.get_active_run()

    if run is None:
        return {
            "success": False,
            "data": None,
            "message": "No active run found",
        }

    run["file_name"] = get_run_file_name(run["run_id"])
    return {
        "success": True,
        "data": run,
    }


def list_runs():
    runs = run_repo.list_runs()
    return [
        {
            "run_id": r["run_id"],
            "run_name": r.get("run_name"),
            "file_name": get_run_file_name(r["run_id"]),
            "source_type": r.get("source_type"),
            "status": r.get("status"),
            "error_message": r.get("error_message"),
            "failed_step": r.get("failed_step"),
            "created_at": str(r.get("created_at")),
        }
        for r in runs
    ]


def search_runs_ipc(query: str):
    """
    Search runs by run_id (DB-backed).
    """
    runs = run_repo.list_runs()

    if not query:
        return list_runs()

    query = query.lower()

    return [
        {
            "run_id": r["run_id"],
            "run_name": r.get("run_name"),
            "file_name": get_run_file_name(r["run_id"]),
            "source_type": r.get("source_type"),
            "status": r.get("status"),
            "error_message": r.get("error_message"),
            "failed_step": r.get("failed_step"),
            "created_at": str(r.get("created_at")),
        }
        for r in runs
        if query in r["run_id"].lower()
    ]
