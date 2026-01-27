# storage/connection.py

import duckdb
from pathlib import Path
from threading import Lock

# Database file path (offline, file-based)
DB_PATH = Path(__file__).parent / "offline_endurance_intelligence.duckdb"

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