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
    return [r["run_id"] for r in runs]