from storage.repositories.run_repo import RunRepository

run_repo = RunRepository()


def get_active_run_ipc():
    run = run_repo.get_active_run()

    if run is None:
        return {
            "success": False,
            "data": None,
            "message": "No active run found",
        }

    return {
        "success": True,
        "data": run,
    }


def list_runs():
    runs = run_repo.list_runs()
    return [{"run_id": r["run_id"]} for r in runs]


def search_runs_ipc(query: str):
    """
    Search runs by run_id (DB-backed).
    """
    runs = run_repo.list_runs()

    if not query:
        return [{"run_id": r["run_id"]} for r in runs]

    query = query.lower()

    return [
        {"run_id": r["run_id"]}
        for r in runs
        if query in r["run_id"].lower()
    ]
