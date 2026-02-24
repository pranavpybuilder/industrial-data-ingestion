from storage.repositories.profiling_repo import ProfilingRepository
from storage.repositories.run_repo import RunRepository

profiling_repo = ProfilingRepository()
run_repo = RunRepository()


def get_data_health_ipc(run_id: str):
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

    results = profiling_repo.get_profiling_results(run_id)
    status = (run.get("status") or "").upper()

    if status == "FAILED":
        return {
            "success": True,
            "data": {
                "run_id": run_id,
                "run_status": status,
                "failed_step": run.get("failed_step"),
                "error_message": run.get("error_message"),
                "profiling_results": results,
                "has_profiling_data": bool(results),
            },
            "message": "Run failed. Failure diagnostics available.",
        }

    return {
        "success": True,
        "data": {
            "run_id": run_id,
            "run_status": status,
            "failed_step": run.get("failed_step"),
            "error_message": run.get("error_message"),
            "profiling_results": results,
            "has_profiling_data": bool(results),
        },
        "message": f"Loaded {len(results)} profiling records",
    }
