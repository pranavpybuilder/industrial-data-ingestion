# app/main.py

"""
Application Entry Point – Offline Industrial Intelligence System.

Responsibilities:
- Initialize DuckDB database
- Expose the PipelineRunner for ingestion
- Provide a CLI interface for testing
- Will be called by the PySide6 desktop shell in production
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.connection import initialize_database
from app.pipeline_runner import PipelineRunner
from utils.logger import get_logger

logger = get_logger("main")


def main() -> None:
    """
    CLI entry point for testing the ingestion pipeline.

    Usage:
        python -m app.main <file_path> [source_type]

    Example:
        python -m app.main data/sample/plc_log.csv plc
        python -m app.main data/sample/report.xlsx report_excel
        python -m app.main data/sample/sap_export.csv
    """

    logger.info("=" * 60)
    logger.info("Offline Industrial Intelligence System – Starting")
    logger.info("=" * 60)

    # Initialize database
    initialize_database()
    logger.info("Database initialized.")

    # Parse CLI arguments
    args = sys.argv[1:]

    if not args:
        logger.info(
            "No file provided. Use: python -m app.main <file> [source_type]"
        )
        logger.info("System is ready. Waiting for desktop UI or IPC calls.")
        return

    file_path = args[0]
    source_type = args[1] if len(args) > 1 else None

    # Run pipeline
    runner = PipelineRunner()

    result = runner.run_single_file(
        file_path=file_path,
        source_type=source_type,
    )

    if result.get("success"):
        logger.info("─" * 40)
        logger.info("PIPELINE RESULT: SUCCESS")
        logger.info(f"  Run ID      : {result['run_id']}")
        logger.info(f"  File        : {result['file_name']}")
        logger.info(f"  Source      : {result['source_type']}")
        logger.info(f"  Rows        : {result['rows']}")
        logger.info(f"  Schema Hash : {result['schema_hash']}")
        logger.info(f"  Features    : {result['feature_count']}")
        health_score = result.get('health_score', None)
        if health_score is not None:
            logger.info(f"  Health Score: {health_score:.1f}/100")
        logger.info(f"  Output      : {result['output_path']}")
        logger.info("─" * 40)
    else:
        logger.error("─" * 40)
        logger.error("PIPELINE RESULT: FAILED")
        logger.error(f"  Error: {result.get('error')}")
        logger.error("─" * 40)


if __name__ == "__main__":
    main()
