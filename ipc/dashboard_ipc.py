from storage.repositories.dashboard_repo import DashboardRepository
from storage.repositories.run_repo import RunRepository

dashboard_repo = DashboardRepository()
run_repo = RunRepository()


def get_dashboard_for_run_ipc(run_id: str):
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
        return {
            "success": True,
            "data": {
                "user_layout": dashboard_repo.get_user_layout(run_id),
            },
            "message": (
                f"Run failed at '{run.get('failed_step') or 'unknown'}': "
                f"{run.get('error_message') or 'No error message recorded'}"
            ),
        }

    dashboard = dashboard_repo.get_dashboard_for_run(run_id)
    user_layout = dashboard_repo.get_user_layout(run_id)

    if dashboard is None:
        return {
            "success": True,
            "data": {"user_layout": user_layout},
            "message": "No dashboard found for run",
        }

    return {
        "success": True,
        "data": {
            **dashboard,
            "user_layout": user_layout,
        },
        "message": "Dashboard loaded",
    }


def save_dashboard_layout_ipc(
    run_id: str,
    blueprint_id: str,
    user_layout: dict,
):
    if not run_id:
        return {
            "success": False,
            "data": None,
            "message": "Run ID is required",
        }

    if not isinstance(user_layout, dict):
        return {
            "success": False,
            "data": None,
            "message": "user_layout must be a JSON object",
        }

    run = run_repo.get_run(run_id)
    if run is None:
        return {
            "success": False,
            "data": None,
            "message": "Run not found",
        }

    dashboard_repo.save_user_layout(
        run_id=run_id,
        blueprint_id=blueprint_id or None,
        user_layout=user_layout,
    )
    return {
        "success": True,
        "data": {"run_id": run_id, "blueprint_id": blueprint_id or None},
        "message": "Dashboard layout saved",
    }


def get_dashboard_layout_ipc(run_id: str):
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

    layout = dashboard_repo.get_user_layout(run_id)
    return {
        "success": True,
        "data": layout,
        "message": "Dashboard layout loaded" if layout else "No saved dashboard layout",
    }
