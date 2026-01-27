# storage/repositories/export_repo.py

from typing import List, Dict
from storage.connection import get_connection


class ExportRepository:
    """
    Repository responsible for storing export history.
    """

    def save_export(
        self,
        export_id: str,
        run_id: str,
        export_type: str,
        scope: str,
        file_path: str,
    ) -> None:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO exports (
                export_id,
                run_id,
                export_type,
                scope,
                file_path
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                export_id,
                run_id,
                export_type,
                scope,
                file_path,
            ),
        )

    def get_exports_for_run(self, run_id: str) -> List[Dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT export_id, export_type, scope, file_path, created_at
            FROM exports
            WHERE run_id = ?
            ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()

        return [
            {
                "export_id": r[0],
                "export_type": r[1],
                "scope": r[2],
                "file_path": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def has_exports(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM exports WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)