# storage/repositories/ingestion_repo.py

import json
from typing import Any, Dict, List, Optional
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
        output_path: Optional[str] = None,
        source_schema_type: Optional[str] = None,
        schema_version: Optional[str] = None,
        schema_drift_detected: bool = False,
        original_column_snapshot: Optional[List[str]] = None,
        normalized_column_snapshot: Optional[List[str]] = None,
        column_mapping: Optional[Dict[str, Any]] = None,
        mapping_decisions: Optional[List[Dict[str, Any]]] = None,
        unmapped_source_columns: Optional[List[str]] = None,
    ) -> None:
        conn = get_connection()

        conn.execute(
            """
            INSERT INTO ingested_files (
                file_id,
                run_id,
                file_name,
                source_type,
                source_schema_type,
                schema_version,
                schema_hash,
                schema_drift_detected,
                original_column_snapshot,
                normalized_column_snapshot,
                column_mapping,
                mapping_decisions,
                unmapped_source_columns,
                row_count,
                output_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                run_id,
                file_name,
                source_type,
                source_schema_type,
                schema_version,
                schema_hash,
                bool(schema_drift_detected),
                json.dumps(original_column_snapshot or []),
                json.dumps(normalized_column_snapshot or []),
                json.dumps(column_mapping or {}),
                json.dumps(mapping_decisions or []),
                json.dumps(unmapped_source_columns or []),
                row_count,
                output_path,
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
                source_schema_type,
                schema_version,
                schema_hash,
                schema_drift_detected,
                original_column_snapshot,
                normalized_column_snapshot,
                column_mapping,
                mapping_decisions,
                unmapped_source_columns,
                row_count,
                output_path,
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
                "source_schema_type": r[3],
                "schema_version": r[4],
                "schema_hash": r[5],
                "schema_drift_detected": bool(r[6]),
                "original_column_snapshot": self._decode_json(r[7], []),
                "normalized_column_snapshot": self._decode_json(r[8], []),
                "column_mapping": self._decode_json(r[9], {}),
                "mapping_decisions": self._decode_json(r[10], []),
                "unmapped_source_columns": self._decode_json(r[11], []),
                "row_count": r[12],
                "output_path": r[13],
                "ingested_at": r[14],
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
        status: str = "PENDING",
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

    def get_latest_output_path(self, run_id: str) -> Optional[str]:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT output_path
            FROM ingested_files
            WHERE run_id = ?
            ORDER BY ingested_at DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def get_latest_schema_hash_for_source(
        self,
        source_type: str,
        source_schema_type: Optional[str] = None,
    ) -> Optional[str]:
        conn = get_connection()

        if source_schema_type:
            row = conn.execute(
                """
                SELECT schema_hash
                FROM ingested_files
                WHERE source_type = ?
                  AND source_schema_type = ?
                  AND schema_hash IS NOT NULL
                ORDER BY ingested_at DESC
                LIMIT 1
                """,
                (source_type, source_schema_type),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT schema_hash
                FROM ingested_files
                WHERE source_type = ?
                  AND schema_hash IS NOT NULL
                ORDER BY ingested_at DESC
                LIMIT 1
                """,
                (source_type,),
            ).fetchone()

        if row is None:
            return None
        return row[0]

    @staticmethod
    def _decode_json(value: Any, default: Any) -> Any:
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return default
