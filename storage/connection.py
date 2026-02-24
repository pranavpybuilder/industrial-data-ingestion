# storage/connection.py

from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

from utils.paths import STORAGE_DIR

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

# Thread-safe singleton connection
_connection = None
_lock = Lock()


def _require_duckdb() -> None:
    if duckdb is not None:
        return
    raise ModuleNotFoundError(
        "Missing dependency 'duckdb'. Install project dependencies with "
        "'python -m pip install -r requirements.txt' and re-run the app."
    ) from _duckdb_import_error


def get_connection() -> "duckdb_types.DuckDBPyConnection":
    """
    Returns a shared DuckDB connection.
    Ensures single connection for the application lifecycle.
    """
    _require_duckdb()

    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                _connection = duckdb.connect(str(DB_PATH))
    return _connection


def initialize_database() -> None:
    """
    Initializes database schema if not already present.
    This function is safe to call multiple times.
    """
    conn = get_connection()
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        raise FileNotFoundError("schema.sql not found in storage directory")

    with open(schema_file, "r", encoding="utf-8") as f:
        conn.execute(f.read())

    _run_migrations(conn)


def _run_migrations(conn: "duckdb_types.DuckDBPyConnection") -> None:
    """
    Apply lightweight forward-only migrations for existing local DBs.
    """
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

    conn.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
    )


def _column_exists(
    conn: "duckdb_types.DuckDBPyConnection",
    table_name: str,
    column_name: str,
) -> bool:
    rows = conn.execute(
        f"PRAGMA table_info('{table_name}')"
    ).fetchall()
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
