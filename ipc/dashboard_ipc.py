from storage.repositories.dashboard_repo import DashboardRepository

dashboard_repo = DashboardRepository()


def get_dashboard_for_run_ipc(run_id: str):
    dashboard = dashboard_repo.get_dashboard_for_run(run_id)

    if dashboard is None:
        return {
            "success": True,
            "data": None,
        }

    return {
        "success": True,
        "data": dashboard,
    }