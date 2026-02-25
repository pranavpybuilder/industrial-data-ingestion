from PySide6.QtCore import QObject, Slot

from ipc.runs_ipc import list_runs, search_runs_ipc
from ipc.ingestion_ipc import upload_file_ipc, get_ingestion_status_ipc
from ipc.insights_ipc import get_insights_ipc
from ipc.dashboard_ipc import (
    get_dashboard_for_run_ipc,
    save_dashboard_layout_ipc,
    get_dashboard_layout_ipc,
)
from ipc.data_health_ipc import get_data_health_ipc
from ipc.exports_ipc import get_exports_for_run_ipc, generate_export_ipc
from ipc.explorer_ipc import get_explorer_data_ipc
from ipc.file_dialog_ipc import select_file_ipc, select_directory_ipc


class FrontendAPI(QObject):
    """
    Qt-exposed frontend API.
    Thin, read-only bridge between UI and backend IPC.
    """

    # -----------------------------
    # Ingestion APIs
    # -----------------------------
    @Slot(str, str, result=dict)
    def upload_file(self, file_path: str, source_type: str = ""):
        return upload_file_ipc(
            file_path=file_path,
            source_type=source_type if source_type else None,
        )

    @Slot(result=dict)
    def select_file(self):
        return select_file_ipc()

    @Slot(result=dict)
    def select_directory(self):
        return select_directory_ipc()

    @Slot(str, result=dict)
    def get_ingestion_status(self, run_id: str):
        return get_ingestion_status_ipc(run_id)

    # -----------------------------
    # Run APIs
    # -----------------------------
    @Slot(result=list)
    def get_runs(self):
        return list_runs()

    @Slot(str, result=list)
    def search_runs(self, query: str):
        return search_runs_ipc(query)

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

    @Slot(str, str, dict, result=dict)
    def save_dashboard_layout(self, run_id: str, blueprint_id: str, user_layout: dict):
        return save_dashboard_layout_ipc(run_id, blueprint_id, user_layout)

    @Slot(str, result=dict)
    def get_dashboard_layout(self, run_id: str):
        return get_dashboard_layout_ipc(run_id)

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

    @Slot(str, str, str, str, result=dict)
    def generate_export(
        self,
        run_id: str,
        export_type: str,
        scope: str = "both",
        output_dir: str = "",
    ):
        return generate_export_ipc(run_id, export_type, scope, output_dir or None)

    @Slot(str, int, result=dict)
    def get_explorer_data(self, run_id: str, limit: int = 500):
        return get_explorer_data_ipc(run_id, limit)


frontend_api = FrontendAPI()
