# storage/repositories/feature_store_repo.py

"""
Repository for persisting feature store data in long format.

Schema (from schema.sql):
    feature_store(run_id, feature_name, feature_value, feature_type, timestamp)
"""

from typing import List, Dict
import pandas as pd
from storage.connection import get_connection


class FeatureStoreRepository:
    """
    Persists and retrieves long-format feature data linked to runs.
    """

    def save_features(self, run_id: str, features: List[Dict]) -> None:
        """
        Save a batch of features in long format.

        Each feature dict must contain:
            feature_name, feature_value, feature_type, timestamp
        """
        conn = get_connection()

        for f in features:
            conn.execute(
                """
                INSERT INTO feature_store (
                    run_id, feature_name, feature_value,
                    feature_type, timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    f["feature_name"],
                    f["feature_value"],
                    f.get("feature_type", "numeric"),
                    f.get("timestamp"),
                ),
            )

    def get_features_for_run(self, run_id: str) -> pd.DataFrame:
        """
        Retrieve all features for a given run.
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT feature_name, feature_value, feature_type, timestamp
            FROM feature_store
            WHERE run_id = ?
            ORDER BY feature_name, timestamp
            """,
            (run_id,),
        ).fetchall()

        if not rows:
            return pd.DataFrame(
                columns=["feature_name", "feature_value", "feature_type", "timestamp"]
            )

        return pd.DataFrame(
            rows,
            columns=["feature_name", "feature_value", "feature_type", "timestamp"],
        )

    def has_features(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM feature_store WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)

    def delete_features_for_run(self, run_id: str) -> None:
        """
        Delete all features for a run (used on re-ingestion).
        """
        conn = get_connection()
        conn.execute(
            "DELETE FROM feature_store WHERE run_id = ?",
            (run_id,),
        )

    def get_feature_summary(self, run_id: str) -> Dict:
        """
        Get a summary of features for a run.
        """
        conn = get_connection()

        row = conn.execute(
            """
            SELECT
                COUNT(*) as total_features,
                COUNT(DISTINCT feature_name) as unique_features
            FROM feature_store
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        return {
            "total_records": row[0] if row else 0,
            "unique_features": row[1] if row else 0,
        }
