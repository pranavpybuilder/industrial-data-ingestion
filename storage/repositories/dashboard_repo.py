# storage/repositories/dashboard_repo.py

from typing import Optional, Dict
import json
import uuid
from storage.connection import get_connection


class DashboardRepository:

    def save_dashboard(
        self,
        dashboard_id: str,
        run_id: str,
        dashboard_state: Dict,
    ) -> None:
        conn = get_connection()
        serialized_state = json.dumps(dashboard_state)

        conn.execute(
            "DELETE FROM dashboards WHERE dashboard_id = ?",
            (dashboard_id,),
        )

        conn.execute(
            """
            INSERT INTO dashboards (dashboard_id, run_id, dashboard_state)
            VALUES (?, ?, ?)
            """,
            (dashboard_id, run_id, serialized_state),
        )

    def save_dashboard_blueprint(
        self,
        run_id: str,
        blueprint: Dict,
    ) -> None:
        """Save dashboard blueprint generated from insights"""
        conn = get_connection()
        
        blueprint_id = blueprint.get("blueprint_id") or f"blueprint_{uuid.uuid4().hex[:12]}"
        if "blueprint_id" not in blueprint:
            blueprint = {**blueprint, "blueprint_id": blueprint_id}
        serialized_blueprint = json.dumps(blueprint)
        
        conn.execute(
            "DELETE FROM dashboards WHERE run_id = ? AND dashboard_id LIKE ?",
            (run_id, "blueprint_%"),
        )
        
        conn.execute(
            """
            INSERT INTO dashboards (dashboard_id, run_id, dashboard_state)
            VALUES (?, ?, ?)
            """,
            (blueprint_id, run_id, serialized_blueprint),
        )

    def get_dashboard_for_run(self, run_id: str) -> Optional[Dict]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT dashboard_id, dashboard_state, saved_at
            FROM dashboards
            WHERE run_id = ? AND dashboard_id LIKE ?
            ORDER BY saved_at DESC
            LIMIT 1
            """,
            (run_id, "blueprint_%"),
        ).fetchone()

        if row is None:
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

        dashboard_state = row[1]
        if isinstance(dashboard_state, str):
            try:
                dashboard_state = json.loads(dashboard_state)
            except json.JSONDecodeError:
                pass

        return {
            "dashboard_id": row[0],
            "dashboard_state": dashboard_state,
            "saved_at": row[2],
        }

    def save_user_layout(
        self,
        run_id: str,
        blueprint_id: Optional[str],
        user_layout: Dict,
    ) -> None:
        conn = get_connection()
        layout_id = f"user_layout_{run_id}"
        payload = json.dumps(user_layout)
        conn.execute(
            """
            DELETE FROM dashboard_layout WHERE layout_id = ?
            """,
            (layout_id,),
        )
        conn.execute(
            """
            INSERT INTO dashboard_layout (layout_id, run_id, blueprint_id, user_saved_layout)
            VALUES (?, ?, ?, ?)
            """,
            (layout_id, run_id, blueprint_id, payload),
        )

    def get_user_layout(self, run_id: str) -> Optional[Dict]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT layout_id, blueprint_id, user_saved_layout, updated_at
            FROM dashboard_layout
            WHERE run_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        user_layout = row[2]
        if isinstance(user_layout, str):
            try:
                user_layout = json.loads(user_layout)
            except json.JSONDecodeError:
                user_layout = None

        if user_layout is None:
            return None

        return {
            "layout_id": row[0],
            "blueprint_id": row[1],
            "user_saved_layout": user_layout,
            "updated_at": row[3],
        }

    def has_dashboard(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM dashboards WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)
