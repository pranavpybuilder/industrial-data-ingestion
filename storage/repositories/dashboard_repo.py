# storage/repositories/dashboard_repo.py

from typing import Optional, Dict
from storage.connection import get_connection


class DashboardRepository:

    def save_dashboard(
        self,
        dashboard_id: str,
        run_id: str,
        dashboard_state: Dict,
    ) -> None:
        conn = get_connection()

        conn.execute(
            "DELETE FROM dashboards WHERE dashboard_id = ?",
            (dashboard_id,),
        )

        conn.execute(
            """
            INSERT INTO dashboards (dashboard_id, run_id, dashboard_state)
            VALUES (?, ?, ?)
            """,
            (dashboard_id, run_id, dashboard_state),
        )

    def save_dashboard_blueprint(
        self,
        run_id: str,
        blueprint: Dict,
    ) -> None:
        """Save dashboard blueprint generated from insights"""
        conn = get_connection()
        
        blueprint_id = blueprint.get("blueprint_id")
        
        conn.execute(
            "DELETE FROM dashboards WHERE run_id = ? AND dashboard_id LIKE ?",
            (run_id, "blueprint_%"),
        )
        
        conn.execute(
            """
            INSERT INTO dashboards (dashboard_id, run_id, dashboard_state)
            VALUES (?, ?, ?)
            """,
            (blueprint_id, run_id, blueprint),
        )

    def get_dashboard_for_run(self, run_id: str) -> Optional[Dict]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT dashboard_id, dashboard_state, saved_at
            FROM dashboards
            WHERE run_id = ?
            ORDER BY saved_at DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "dashboard_id": row[0],
            "dashboard_state": row[1],
            "saved_at": row[2],
        }

    def has_dashboard(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM dashboards WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)