-- storage/schema.sql

-- =====================================================
-- RUNS
-- =====================================================
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL
);

-- =====================================================
-- INGESTED FILES METADATA
-- =====================================================
CREATE TABLE IF NOT EXISTS ingested_files (
    file_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    schema_hash TEXT,
    row_count INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- FEATURE STORE (LONG FORMAT)
-- =====================================================
CREATE TABLE IF NOT EXISTS feature_store (
    run_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value DOUBLE,
    feature_type TEXT,
    timestamp TIMESTAMP
);

-- =====================================================
-- PROFILING RESULTS (DATA HEALTH)
-- =====================================================
CREATE TABLE IF NOT EXISTS profiling_results (
    run_id TEXT NOT NULL,
    column_name TEXT NOT NULL,
    missing_percentage DOUBLE,
    outlier_count INTEGER,
    detected_type TEXT,
    health_status TEXT
);

-- =====================================================
-- INSIGHTS (RULE + ML)
-- =====================================================
CREATE TABLE IF NOT EXISTS insights (
    insight_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    confidence DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DASHBOARD STATE STORAGE
-- =====================================================
CREATE TABLE IF NOT EXISTS dashboards (
    dashboard_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    dashboard_state JSON NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- EXPORT HISTORY
-- =====================================================
CREATE TABLE IF NOT EXISTS exports (
    export_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    export_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);