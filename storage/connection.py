# storage/connection.py

import atexit
import time
import logging
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

from utils.paths import STORAGE_DIR

logger = logging.getLogger(__name__)

try:
    import duckdb
except ModuleNotFoundError as exc:
    duckdb = None
    _duckdb_import_error = exc
else:
    _duckdb_import_error = None

if TYPE_CHECKING:
    import duckdb as duckdb_types

DB_PATH = STORAGE_DIR / "offline_endurance_intelligence.duckdb"

# ── Singleton state ────────────────────────────────────────────────────────────
_connection = None
_lock = Lock()

# Retry config
_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 1.0


def _require_duckdb() -> None:
    if duckdb is not None:
        return
    raise ModuleNotFoundError(
        "Missing dependency 'duckdb'. Install project dependencies with "
        "'python -m pip install -r requirements.txt' and re-run the app."
    ) from _duckdb_import_error


def _delete_wal(db_path: Path) -> bool:
    """Delete the WAL file if it exists. Returns True if deleted."""
    wal_path = Path(str(db_path) + ".wal")
    if not wal_path.exists():
        return False
    try:
        wal_path.unlink()
        logger.warning(f"[DB] Deleted stale/corrupt WAL file: {wal_path}")
        return True
    except OSError as e:
        logger.error(f"[DB] Could not delete WAL file: {wal_path} — {e}")
        return False


def _delete_db_and_wal(db_path: Path) -> None:
    """
    Delete both the .duckdb and .wal files so the DB is recreated fresh.
    Used as last resort when WAL is corrupt and unrecoverable.
    """
    for path in [db_path, Path(str(db_path) + ".wal")]:
        if path.exists():
            try:
                path.unlink()
                logger.warning(f"[DB] Deleted corrupt DB file: {path}")
            except OSError as e:
                logger.error(f"[DB] Could not delete: {path} — {e}")


def get_connection() -> "duckdb_types.DuckDBPyConnection":
    """
    Returns a shared DuckDB connection (singleton).

    Handles three failure modes automatically:
      1. File locked by another process → retry with delay
      2. Corrupt WAL file → delete WAL and retry
      3. Corrupt DB + WAL → delete both, recreate fresh DB

    Raises:
        RuntimeError: if DB cannot be opened after all recovery attempts.
        ModuleNotFoundError: if duckdb is not installed.
    """
    _require_duckdb()

    global _connection

    # Fast path — already connected
    if _connection is not None:
        return _connection

    with _lock:
        if _connection is not None:
            return _connection

        # Ensure storage directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info(
                    f"[DB] Opening DuckDB (attempt {attempt}/{_MAX_RETRIES}): {DB_PATH}"
                )
                _connection = duckdb.connect(str(DB_PATH))
                logger.info("[DB] Connection established successfully.")
                return _connection

            except Exception as exc:
                last_error = exc
                error_msg = str(exc).lower()

                # ── Case 1: File locked by another running process ────────────
                is_lock_error = (
                    "cannot open file" in error_msg
                    or "being used by another process" in error_msg
                    or "io error" in error_msg
                    or "ioerror" in error_msg
                )

                # ── Case 2: WAL file is corrupt (your current error) ──────────
                is_wal_error = (
                    "replaying wal" in error_msg
                    or "failure while replaying" in error_msg
                    or "databasemanager" in error_msg
                    or "internal error" in error_msg
                    or "assertion failure" in error_msg
                )

                if is_wal_error:
                    logger.warning(
                        f"[DB] Corrupt WAL file detected on attempt {attempt}. "
                        f"Attempting auto-recovery..."
                    )
                    if attempt == 1:
                        # First: try deleting only the WAL — DB data is preserved
                        deleted = _delete_wal(DB_PATH)
                        if deleted:
                            logger.info("[DB] WAL deleted — retrying connection...")
                            continue
                    if attempt == 2:
                        # Second: WAL delete didn't help — nuke both files
                        # DB will be recreated fresh from schema.sql
                        logger.warning(
                            "[DB] WAL-only recovery failed. "
                            "Deleting corrupt database and WAL for fresh start. "
                            "All run data will be reset."
                        )
                        _delete_db_and_wal(DB_PATH)
                        continue

                elif is_lock_error:
                    logger.warning(
                        f"[DB] File locked (attempt {attempt}/{_MAX_RETRIES}). "
                        f"Another instance may be running. "
                        f"Retrying in {_RETRY_DELAY_SEC}s..."
                    )
                    if attempt < _MAX_RETRIES:
                        time.sleep(_RETRY_DELAY_SEC)
                    continue

                else:
                    # Unknown error — don't retry
                    logger.error(f"[DB] Unexpected error: {exc}")
                    raise

        # ── All retries exhausted ─────────────────────────────────────────────
        raise RuntimeError(
            f"\n\n{'='*60}\n"
            f"  DATABASE ERROR — Cannot open database\n"
            f"{'='*60}\n"
            f"  File: {DB_PATH}\n\n"
            f"  POSSIBLE CAUSES & FIXES:\n\n"
            f"  1. Another instance is running:\n"
            f"     → Open Task Manager (Ctrl+Shift+Esc)\n"
            f"     → Find 'OfflineIndustrialIntelligence.exe'\n"
            f"     → Right-click → End Task\n"
            f"     → Relaunch the app\n\n"
            f"  2. Database files are corrupt:\n"
            f"     → Delete these files manually:\n"
            f"       {DB_PATH}\n"
            f"       {DB_PATH}.wal\n"
            f"     → Relaunch — the DB will be recreated fresh\n\n"
            f"  3. If problem persists: restart your computer.\n"
            f"{'='*60}\n\n"
            f"  Technical detail: {last_error}\n"
        ) from last_error


def close_connection() -> None:
    """
    Explicitly close the DuckDB connection and release the file lock.

    Register with atexit so this always runs on process exit:
        import atexit
        atexit.register(close_connection)
    """
    global _connection
    with _lock:
        if _connection is not None:
            try:
                _connection.close()
                logger.info("[DB] Connection closed cleanly.")
            except Exception as exc:
                logger.warning(f"[DB] Error while closing connection: {exc}")
            finally:
                _connection = None


def initialize_database() -> None:
    """
    Initializes database schema if not already present.
    Safe to call multiple times.
    """
    conn = get_connection()
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        raise FileNotFoundError("schema.sql not found in storage directory")

    with open(schema_file, "r", encoding="utf-8") as f:
        conn.execute(f.read())

    _run_migrations(conn)


def _run_migrations(conn: "duckdb_types.DuckDBPyConnection") -> None:
    """Apply lightweight forward-only migrations for existing local DBs."""
    _ensure_column(conn, "runs", "error_message TEXT")
    _ensure_column(conn, "runs", "failed_step TEXT")
    _normalize_run_statuses(conn)

    _ensure_column(conn, "ingested_files", "output_path TEXT")
    _ensure_column(conn, "ingested_files", "source_schema_type TEXT")
    _ensure_column(conn, "ingested_files", "schema_version TEXT")
    _ensure_column(
        conn, "ingested_files", "schema_drift_detected BOOLEAN DEFAULT FALSE"
    )
    _ensure_column(conn, "ingested_files", "original_column_snapshot JSON")
    _ensure_column(conn, "ingested_files", "normalized_column_snapshot JSON")
    _ensure_column(conn, "ingested_files", "column_mapping JSON")
    _ensure_column(conn, "ingested_files", "mapping_decisions JSON")
    _ensure_column(conn, "ingested_files", "unmapped_source_columns JSON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_layout (
            layout_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            blueprint_id TEXT,
            user_saved_layout JSON NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _ensure_column(
    conn: "duckdb_types.DuckDBPyConnection",
    table_name: str,
    column_definition: str,
) -> None:
    column_name = column_definition.split()[0]
    if _column_exists(conn, table_name, column_name):
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")


def _column_exists(
    conn: "duckdb_types.DuckDBPyConnection",
    table_name: str,
    column_name: str,
) -> bool:
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return any(str(row[1]).lower() == column_name.lower() for row in rows)


def _normalize_run_statuses(conn: "duckdb_types.DuckDBPyConnection") -> None:
    conn.execute(
        """
        UPDATE runs
        SET status = CASE
            WHEN upper(status) = 'CREATED' THEN 'PENDING'
            WHEN upper(status) = 'PROCESSING' THEN 'RUNNING'
            ELSE upper(status)
        END
        """
    )


# ── Ensure clean shutdown on process exit ──────────────────────────────────────
atexit.register(close_connection)