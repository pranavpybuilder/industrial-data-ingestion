from storage.repositories.insight_repo import InsightRepository
from storage.repositories.run_repo import RunRepository

insight_repo = InsightRepository()
run_repo = RunRepository()


def get_insights_ipc(run_id: str):
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

    if str(run.get("status", "")).upper() == "FAILED":
        failed_step = run.get("failed_step") or "unknown"
        error_message = run.get("error_message") or "No error message recorded"
        return {
            "success": True,
            "data": [],
            "message": f"Run failed at '{failed_step}': {error_message}",
        }

    insights = insight_repo.get_insights(run_id)

    return {
        "success": True,
        "data": insights,
        "message": f"Loaded {len(insights)} insights",
    }
