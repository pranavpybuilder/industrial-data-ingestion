# storage/repositories/profiling_repo.py

from typing import List, Dict
from storage.connection import get_connection


class ProfilingRepository:

    def save_profiling_results(self, run_id: str, results: List[Dict]) -> None:
        conn = get_connection()

        conn.execute(
            "DELETE FROM profiling_results WHERE run_id = ?",
            (run_id,),
        )

        for r in results:
            conn.execute(
                """
                INSERT INTO profiling_results (
                    run_id,
                    column_name,
                    missing_percentage,
                    outlier_count,
                    detected_type,
                    health_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    r["column_name"],
                    r["missing_percentage"],
                    r["outlier_count"],
                    r["detected_type"],
                    r["health_status"],
                ),
            )

    def get_profiling_results(self, run_id: str) -> List[Dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT
                column_name,
                missing_percentage,
                outlier_count,
                detected_type,
                health_status
            FROM profiling_results
            WHERE run_id = ?
            ORDER BY column_name
            """,
            (run_id,),
        ).fetchall()

        return [
            {
                "column_name": r[0],
                "missing_percentage": r[1],
                "outlier_count": r[2],
                "detected_type": r[3],
                "health_status": r[4],
            }
            for r in rows
        ]

    def has_profiling_data(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM profiling_results WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)