from PySide6.QtCore import QObject, Slot

from ipc.runs_ipc import list_runs
from ipc.insights_ipc import get_insights_ipc
from ipc.dashboard_ipc import get_dashboard_for_run_ipc
from ipc.data_health_ipc import get_data_health_ipc
from ipc.exports_ipc import get_exports_for_run_ipc


class FrontendAPI(QObject):
    """
    Qt-exposed frontend API.
    Thin, read-only bridge between UI and backend IPC.
    """

    # -----------------------------
    # Run APIs
    # -----------------------------
    @Slot(result=list)
    def get_runs(self):
        return list_runs()

    # -----------------------------
    # Insights APIs
    # -----------------------------
    @Slot(str, result=dict)
    def get_insights(self, run_id: str):
        return get_insights_ipc(run_id)

    # -----------------------------
    # Dashboard APIs
    # -----------------------------
    @Slot(str, result=dict)
    def get_dashboard(self, run_id: str):
        return get_dashboard_for_run_ipc(run_id)

    # -----------------------------
    # Data Health APIs
    # -----------------------------
    @Slot(str, result=dict)
    def get_data_health(self, run_id: str):
        return get_data_health_ipc(run_id)

    # -----------------------------
    # Exports APIs
    # -----------------------------
    @Slot(str, result=dict)
    def get_exports(self, run_id: str):
        return get_exports_for_run_ipc(run_id)


frontend_api = FrontendAPI()