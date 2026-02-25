# storage/repositories/run_repo.py

from typing import List, Optional, Dict
from storage.connection import get_connection


class RunStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    # Backward-compatible aliases for older callers/records.
    CREATED = PENDING
    PROCESSING = RUNNING


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
        status: str = RunStatus.PENDING,
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
            INSERT INTO runs (run_id, run_name, source_type, status, error_message, failed_step)
            VALUES (?, ?, ?, ?, NULL, NULL)
            """,
            (run_id, run_name, source_type, status),
        )

    # --------------------------------------------------
    # UPDATE RUN STATUS
    # --------------------------------------------------
    def update_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        failed_step: Optional[str] = None,
    ) -> None:
        conn = get_connection()

        if status == RunStatus.FAILED:
            result = conn.execute(
                """
                UPDATE runs
                SET status = ?, error_message = ?, failed_step = ?
                WHERE run_id = ?
                """,
                (status, error_message, failed_step, run_id),
            )
        else:
            result = conn.execute(
                """
                UPDATE runs
                SET status = ?, error_message = NULL, failed_step = NULL
                WHERE run_id = ?
                """,
                (status, run_id),
            )

        if result.rowcount == 0:
            raise ValueError(f"Run with ID '{run_id}' not found.")

    def mark_failed(
        self,
        run_id: str,
        error_message: str,
        failed_step: str,
    ) -> None:
        self.update_status(
            run_id=run_id,
            status=RunStatus.FAILED,
            error_message=error_message,
            failed_step=failed_step,
        )

    # --------------------------------------------------
    # GET RUN
    # --------------------------------------------------
    def get_run(self, run_id: str) -> Optional[Dict]:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status, error_message, failed_step
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
            "error_message": row[5],
            "failed_step": row[6],
        }

    # --------------------------------------------------
    # LIST ALL RUNS
    # --------------------------------------------------
    def list_runs(self) -> List[Dict]:
        conn = get_connection()

        rows = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status, error_message, failed_step
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
                "error_message": r[5],
                "failed_step": r[6],
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
            (RunStatus.SUCCESS, RunStatus.PENDING),
        )

        # Set selected run as RUNNING
        conn.execute(
            """
            UPDATE runs
            SET status = ?
            WHERE run_id = ?
            """,
            (RunStatus.RUNNING, run_id),
        )

    # --------------------------------------------------
    # GET LATEST RUN
    # --------------------------------------------------
    def get_latest_run(self) -> Optional[Dict]:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status, error_message, failed_step
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
            "error_message": row[5],
            "failed_step": row[6],
        }

    # --------------------------------------------------
    # GET ACTIVE RUN (RUNNING status)
    # --------------------------------------------------
    def get_active_run(self) -> Optional[Dict]:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT run_id, run_name, source_type, created_at, status, error_message, failed_step
            FROM runs
            WHERE status IN (?, ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (RunStatus.RUNNING, "PROCESSING"),
        ).fetchone()

        if row is None:
            return None

        return {
            "run_id": row[0],
            "run_name": row[1],
            "source_type": row[2],
            "created_at": row[3],
            "status": row[4],
            "error_message": row[5],
            "failed_step": row[6],
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
