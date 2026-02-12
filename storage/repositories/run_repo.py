# storage/repositories/run_repo.py

from typing import List, Optional, Dict
from storage.connection import get_connection


class RunStatus:
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RunRepository:
    """
    Repository responsible for managing analytical run lifecycle.
    Production-ready, deterministic, and safe.
    """

    # --------------------------------------------------
    # CREATE RUN
    # --------------------------------------------------
    def create_run(
        self,
        run_id: str,
        run_name: str,
        source_type: str,
        status: str = RunStatus.CREATED,
    ) -> None:
        conn = get_connection()

        existing = conn.execute(
            "SELECT 1 FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if existing:
            raise ValueError(f"Run with ID '{run_id}' already exists.")

        conn.execute(
            """
            INSERT INTO runs (run_id, run_name, source_type, status)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, run_name, source_type, status),
        )

    # --------------------------------------------------
    # UPDATE RUN STATUS
    # --------------------------------------------------
    def update_status(self, run_id: str, status: str) -> None:
        conn = get_connection()

        result = conn.execute(
            """
            UPDATE runs
            SET status = ?
            WHERE run_id = ?
            """,
            (status, run_id),
        )

        if result.rowcount == 0:
            raise ValueError(f"Run with ID '{run_id}' not found.")

    # --------------------------------------------------
    # GET RUN
    # --------------------------------------------------
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

    # --------------------------------------------------
    # LIST ALL RUNS
    # --------------------------------------------------
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

    # --------------------------------------------------
    # SET ACTIVE RUN (Only one active at a time)
    # --------------------------------------------------
    def set_active_run(self, run_id: str) -> None:
        conn = get_connection()

        # Ensure run exists
        existing = conn.execute(
            "SELECT 1 FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if not existing:
            raise ValueError(f"Run with ID '{run_id}' does not exist.")

        # Reset all active runs
        conn.execute(
            """
            UPDATE runs
            SET status = ?
            WHERE status = ?
            """,
            (RunStatus.SUCCESS, RunStatus.CREATED),
        )

        # Set selected run as PROCESSING
        conn.execute(
            """
            UPDATE runs
            SET status = ?
            WHERE run_id = ?
            """,
            (RunStatus.PROCESSING, run_id),
        )

    # --------------------------------------------------
    # GET LATEST RUN
    # --------------------------------------------------
    def get_latest_run(self) -> Optional[Dict]:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status
            FROM runs
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

    # --------------------------------------------------
    # GET ACTIVE RUN (PROCESSING status)
    # --------------------------------------------------
    def get_active_run(self) -> Optional[Dict]:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status
            FROM runs
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (RunStatus.PROCESSING,),
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

    # --------------------------------------------------
    # DELETE RUN (SAFE)
    # --------------------------------------------------
    def delete_run(self, run_id: str) -> None:
        conn = get_connection()

        conn.execute(
            "DELETE FROM runs WHERE run_id = ?",
            (run_id,),
        )