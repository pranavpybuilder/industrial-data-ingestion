"""
Preload / Bridge layer between the desktop shell and the frontend renderer.

This module exposes a controlled, read-only API to the frontend
using Qt WebChannel. All methods return mock data and are safe
for offline frontend development.

This file MUST NOT:
- Access backend layers
- Perform business logic
- Read/write files or databases
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import QObject, Slot


class FrontendAPI(QObject):
    """
    Qt-exposed frontend API.

    All methods are:
    - Read-only
    - Deterministic
    - JSON-serializable
    """

    def __init__(self) -> None:
        super().__init__()

    # -----------------------------
    # Run / Dataset APIs
    # -----------------------------

    @Slot(result=list)
    def get_runs(self) -> List[Dict[str, Any]]:
        return [
            {
                "run_id": "RUN_2026_01_10_001",
                "source_type": "excel",
                "file_names": ["excel_maintenance_jan.xlsx"],
                "ingested_at": datetime(2026, 1, 10, 14, 30).isoformat(),
                "status": "SUCCESS",
            },
            {
                "run_id": "RUN_2026_01_11_001",
                "source_type": "rfid",
                "file_names": ["rfid_logs_day2.csv"],
                "ingested_at": datetime(2026, 1, 11, 9, 15).isoformat(),
                "status": "SUCCESS",
            },
        ]

    # -----------------------------
    # Insights APIs
    # -----------------------------

    @Slot(str, result=list)
    def get_insights(self, run_id: str) -> List[Dict[str, Any]]:
        if run_id == "RUN_2026_01_10_001":
            return [
                {
                    "insight_id": "INSIGHT_001",
                    "title": "Repeated Downtime Detected",
                    "severity": "HIGH",
                    "category": "Downtime",
                    "entity_scope": "Machine_A",
                    "time_window": "2026-01-09 to 2026-01-10",
                    "explanation": {
                        "rule": "Downtime exceeded threshold for 3 consecutive shifts",
                        "ml": "Anomalous deviation from historical baseline",
                    },
                }
            ]
        return []

    # -----------------------------
    # Dashboard APIs
    # -----------------------------

    @Slot(str, result=list)
    def get_dashboards(self, run_id: str) -> List[Dict[str, Any]]:
        if run_id == "RUN_2026_01_10_001":
            return [
                {
                    "dashboard_id": "DASH_001",
                    "name": "Maintenance Overview",
                    "charts": [
                        {
                            "chart_id": "CHART_001",
                            "metric": "downtime_minutes",
                            "chart_type": "line",
                            "allowed_chart_types": ["line", "bar"],
                        }
                    ],
                }
            ]
        return []

    # -----------------------------
    # Reports APIs
    # -----------------------------

    @Slot(result=list)
    def get_reports(self) -> List[Dict[str, Any]]:
        return [
            {
                "report_id": "REP_001",
                "run_id": "RUN_2026_01_10_001",
                "export_scope": "insights+dashboards",
                "format": "pdf",
                "created_at": datetime(2026, 1, 10, 18, 0).isoformat(),
            }
        ]


# Single, shared instance
frontend_api = FrontendAPI()
