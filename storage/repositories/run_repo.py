# storage/repositories/run_repo.py

from typing import List, Optional, Dict
from storage.connection import get_connection


class RunRepository:
    """
    Repository responsible for managing analytical runs.
    """

    def create_run(
        self,
        run_id: str,
        run_name: str,
        source_type: str,
        status: str = "active",
    ) -> None:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO runs (run_id, run_name, source_type, status)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, run_name, source_type, status),
        )

    def update_status(self, run_id: str, status: str) -> None:
        conn = get_connection()
        conn.execute(
            """
            UPDATE runs
            SET status = ?
            WHERE run_id = ?
            """,
            (status, run_id),
        )

    def get_run(self, run_id: str) -> Optional[Dict]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "run_id": row[0],
            "run_name": row[1],
            "source_type": row[2],
            "created_at": row[3],
            "status": row[4],
        }

    def list_runs(self) -> List[Dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status
            FROM runs
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [
            {
                "run_id": r[0],
                "run_name": r[1],
                "source_type": r[2],
                "created_at": r[3],
                "status": r[4],
            }
            for r in rows
        ]

    def get_active_run(self) -> Optional[Dict]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status
            FROM runs
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return None

        return {
            "run_id": row[0],
            "run_name": row[1],
            "source_type": row[2],
            "created_at": row[3],
            "status": row[4],
        }