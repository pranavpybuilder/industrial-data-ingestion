# storage/repositories/ingestion_repo.py

from typing import List, Dict, Optional
from storage.connection import get_connection
from datetime import datetime
from storage.connection import get_connection



class IngestionRepository:
    """
    Repository responsible for persisting ingestion metadata
    for each analytical run.
    """

    def save_ingested_file(
        self,
        file_id: str,
        run_id: str,
        file_name: str,
        source_type: str,
        schema_hash: Optional[str],
        row_count: int,
    ) -> None:
        conn = get_connection()

        conn.execute(
            """
            INSERT INTO ingested_files (
                file_id,
                run_id,
                file_name,
                source_type,
                schema_hash,
                row_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                run_id,
                file_name,
                source_type,
                schema_hash,
                row_count,
            ),
        )

    def get_ingested_files(self, run_id: str) -> List[Dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT
                file_id,
                file_name,
                source_type,
                schema_hash,
                row_count,
                ingested_at
            FROM ingested_files
            WHERE run_id = ?
            ORDER BY ingested_at
            """,
            (run_id,),
        ).fetchall()

        return [
            {
                "file_id": r[0],
                "file_name": r[1],
                "source_type": r[2],
                "schema_hash": r[3],
                "row_count": r[4],
                "ingested_at": r[5],
            }
            for r in rows
        ]

    def has_ingestion_data(self, run_id: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM ingested_files WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        return bool(row and row[0] > 0)

    def delete_ingestion_for_run(self, run_id: str) -> None:
        """
        Deletes all ingestion metadata for a run.
        Used when ingestion is retried.
        """
        conn = get_connection()
        conn.execute(
            "DELETE FROM ingested_files WHERE run_id = ?",
            (run_id,),
        )

    def create_run(
        self,
        run_id: str,
        run_name: str,
        source_type: str,
        status: str = "CREATED",
    ) -> None:
        conn = get_connection()

        conn.execute(
            """
            INSERT INTO runs (
                run_id,
                run_name,
                source_type,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                run_id,
                run_name,
                source_type,
                status,
            ),
        )

    def update_run_status(self, run_id: str, status: str) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE runs SET status = ? WHERE run_id = ?",
            (status, run_id),
        )