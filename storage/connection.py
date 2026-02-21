# storage/connection.py

import os
import sys
import duckdb
from pathlib import Path
from threading import Lock

# ─── Embedded schema SQL (fallback when .sql file is not bundled) ───
_EMBEDDED_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingested_files (
    file_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    schema_hash TEXT,
    row_count INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_store (
    run_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value DOUBLE,
    feature_type TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiling_results (
    run_id TEXT NOT NULL,
    column_name TEXT NOT NULL,
    missing_percentage DOUBLE,
    outlier_count INTEGER,
    detected_type TEXT,
    health_status TEXT
);

CREATE TABLE IF NOT EXISTS insights (
    insight_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    confidence DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboards (
    dashboard_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    dashboard_state JSON NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exports (
    export_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    export_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _get_project_root() -> Path:
    """
    Resolve the project root in both development and frozen (PyInstaller) modes.
    """
    # PyInstaller frozen executable
    if getattr(sys, "frozen", False):
        # sys._MEIPASS is the temp extraction dir for --onefile
        # For --onedir, the exe dir is the base
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base
    # Development: connection.py lives in <project>/storage/
    return Path(__file__).resolve().parent.parent


def _resolve_storage_dir() -> Path:
    """
    Determine writable storage directory.
    In dev: use <project>/storage/
    In production: use AppData/Local/<AppName>/storage/
    """
    if getattr(sys, "frozen", False):
        app_name = "OfflineIndustrialIntelligence"
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / app_name
        storage = base / "storage"
        storage.mkdir(parents=True, exist_ok=True)
        return storage
    else:
        # Development mode – use the local storage/ directory
        local_storage = Path(__file__).resolve().parent
        return local_storage


# ─── Database file path ───
_STORAGE_DIR = _resolve_storage_dir()
DB_PATH = _STORAGE_DIR / "offline_endurance_intelligence.duckdb"

# Thread-safe singleton connection
_connection = None
_lock = Lock()


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a shared DuckDB connection.
    Ensures single connection for the application lifecycle.
    """
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
                _connection = duckdb.connect(str(DB_PATH))
    return _connection


def _find_schema_sql() -> str | None:
    """
    Try multiple locations to find schema.sql.
    Returns the SQL content or None if not found.
    """
    candidates = [
        # 1. Same directory as this file (development)
        Path(__file__).resolve().parent / "schema.sql",
        # 2. Project root / storage (development)
        _get_project_root() / "storage" / "schema.sql",
        # 3. PyInstaller bundle (--add-data "storage/schema.sql;storage")
        Path(getattr(sys, "_MEIPASS", "")) / "storage" / "schema.sql",
        # 4. Next to executable
        Path(sys.executable).parent / "storage" / "schema.sql",
        # 5. Writable storage dir
        _STORAGE_DIR / "schema.sql",
    ]

    for path in candidates:
        try:
            if path.exists():
                return path.read_text(encoding="utf-8")
        except Exception:
            continue

    return None


def initialize_database() -> None:
    """
    Initializes database schema if not already present.
    This function is safe to call multiple times.
    Uses schema.sql file when available, falls back to embedded SQL.
    """
    conn = get_connection()

    schema_sql = _find_schema_sql()
    if schema_sql:
        conn.execute(schema_sql)
        return

    # Fallback: use embedded schema (always available, even in frozen builds)
    conn.execute(_EMBEDDED_SCHEMA)