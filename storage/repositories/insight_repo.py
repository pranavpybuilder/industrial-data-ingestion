# storage/repositories/insight_repo.py

from typing import List, Dict
from storage.connection import get_connection


class InsightRepository:

    def save_insights(self, run_id: str, insights: List[Dict]) -> None:
        conn = get_connection()

        conn.execute(
            "DELETE FROM insights WHERE run_id = ?",
            (run_id,),
        )

        for insight in insights:
            conn.execute(
                """
                INSERT INTO insights (
                    insight_id, run_id, insight_type, summary, confidence
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    insight["insight_id"],
                    run_id,
                    insight["insight_type"],
                    insight["summary"],
                    insight.get("confidence"),
                ),
            )

    def get_insights(self, run_id: str) -> List[Dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT insight_id, insight_type, summary, confidence, created_at
            FROM insights
            WHERE run_id = ?
            ORDER BY created_at
            """,
            (run_id,),
        ).fetchall()

        return [
            {
                "insight_id": r[0],
                "insight_type": r[1],
                "summary": r[2],
                "confidence": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def has_insights(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM insights WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)