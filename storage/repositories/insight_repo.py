# storage/repositories/insight_repo.py

from typing import List, Dict
import json
from storage.connection import get_connection


class InsightRepository:

    def save_insights(self, run_id: str, insights: List[Dict]) -> None:
        """Save unified insights with all attributes"""
        conn = get_connection()

        conn.execute(
            "DELETE FROM insights WHERE run_id = ?",
            (run_id,),
        )

        for insight in insights:
            # Store full insight as JSON in summary field
            insight_json = json.dumps(insight)
            
            conn.execute(
                """
                INSERT INTO insights (
                    insight_id, run_id, insight_type, summary, confidence
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    insight.get("insight_id"),
                    run_id,
                    insight.get("source", "UNKNOWN"),  # source as insight_type
                    insight_json,  # full insight as JSON
                    insight.get("priority_score", 0),  # priority_score as confidence
                ),
            )

    def get_insights(self, run_id: str) -> List[Dict]:
        """Retrieve unified insights with all attributes"""
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT insight_id, summary, confidence, created_at
            FROM insights
            WHERE run_id = ?
            ORDER BY confidence DESC, created_at
            """,
            (run_id,),
        ).fetchall()

        insights = []
        for row in rows:
            try:
                # Deserialize full insight from JSON
                insight = json.loads(row[1])
                insight["created_at"] = row[3]
                insights.append(insight)
            except (json.JSONDecodeError, TypeError):
                # Fallback if not valid JSON
                insights.append({
                    "insight_id": row[0],
                    "summary": row[1],
                    "confidence": row[2],
                    "created_at": row[3],
                })
        
        return insights

    def get_insights_by_severity(
        self,
        run_id: str,
        severity: str,
    ) -> List[Dict]:
        """Get insights filtered by severity"""
        all_insights = self.get_insights(run_id)
        return [i for i in all_insights if i.get("severity") == severity]

    def get_insights_by_resource(
        self,
        run_id: str,
        resource: str,
    ) -> List[Dict]:
        """Get insights filtered by resource"""
        all_insights = self.get_insights(run_id)
        return [i for i in all_insights if i.get("resource") == resource]

    def get_critical_insights(self, run_id: str) -> List[Dict]:
        """Get only CRITICAL severity insights"""
        return self.get_insights_by_severity(run_id, "CRITICAL")

    def has_insights(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM insights WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)