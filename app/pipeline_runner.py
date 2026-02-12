# app/pipeline_runner.py

"""
Pipeline Runner – End-to-end orchestrator for Module 1: Ingestion Layer.

Flow:
    1. Create a new analytical run
    2. Ingest the uploaded file (validate, persist parquet)
    3. Save ingestion metadata to DuckDB
    4. Populate feature store (long-format) from ingested data
    5. Update run status

This is called by main.py and the IPC layer.
Fully offline. No network calls.
"""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

from storage.connection import initialize_database
from storage.repositories.run_repo import RunRepository, RunStatus
from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.feature_store_repo import FeatureStoreRepository
from ingestion.upload_handler import handle_file_upload
from utils.logger import get_logger

logger = get_logger(__name__)

run_repo = RunRepository()
ingestion_repo = IngestionRepository()
feature_store_repo = FeatureStoreRepository()


class PipelineRunner:
    """
    Orchestrates the full ingestion pipeline for one or more files.
    """

    def __init__(self) -> None:
        initialize_database()
        logger.info("Pipeline runner initialized. Database ready.")

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def run_single_file(
        self,
        file_path: str,
        source_type: Optional[str] = None,
        run_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a single file through the full pipeline.

        Parameters
        ----------
        file_path : str
            Absolute path to the file
        source_type : str, optional
            sap / plc / rfid / report_excel / operational_excel
        run_name : str, optional
            Human-readable run name

        Returns
        -------
        dict with success, run_id, ingestion metadata, feature count
        """

        # ── Step 1: Ingest file ──
        ingestion_result = handle_file_upload(
            file_path=file_path,
            source_type=source_type,
        )

        if not ingestion_result.get("success"):
            return {
                "success": False,
                "error": ingestion_result.get("error"),
            }

        run_id = ingestion_result["run_id"]
        resolved_source = ingestion_result["source"]
        file_name = ingestion_result.get("file_name", Path(file_path).name)

        if run_name is None:
            run_name = f"{resolved_source}_{file_name}"

        # ── Step 2: Create run in DB ──
        try:
            run_repo.create_run(
                run_id=run_id,
                run_name=run_name,
                source_type=resolved_source,
                status=RunStatus.PROCESSING,
            )
            logger.info(f"Run created: {run_id}")
        except Exception as exc:
            logger.error(f"Failed to create run: {exc}")
            return {"success": False, "error": str(exc)}

        # ── Step 3: Save ingestion metadata to DB ──
        try:
            file_id = str(uuid.uuid4())[:12]
            ingestion_repo.save_ingested_file(
                file_id=file_id,
                run_id=run_id,
                file_name=file_name,
                source_type=resolved_source,
                schema_hash=ingestion_result.get("schema_hash"),
                row_count=ingestion_result.get("rows", 0),
            )
            logger.info(
                f"Ingestion metadata saved: {file_name}, "
                f"{ingestion_result['rows']} rows"
            )
        except Exception as exc:
            logger.error(f"Failed to save ingestion metadata: {exc}")
            run_repo.update_status(run_id, RunStatus.FAILED)
            return {"success": False, "error": str(exc)}

        # ── Step 4: Populate feature store ──
        feature_count = 0
        try:
            feature_count = self._populate_features(
                run_id=run_id,
                source_type=resolved_source,
                output_path=ingestion_result.get("output_path"),
            )
            logger.info(
                f"Feature store populated: {feature_count} features"
            )
        except Exception as exc:
            # Feature store population is best-effort for Module 1
            logger.warning(
                f"Feature store population failed (non-fatal): {exc}"
            )

        # ── Step 5: Mark run as successful ──
        run_repo.update_status(run_id, RunStatus.SUCCESS)
        logger.info(f"Pipeline complete for run {run_id}")

        return {
            "success": True,
            "run_id": run_id,
            "file_name": file_name,
            "source_type": resolved_source,
            "rows": ingestion_result.get("rows", 0),
            "schema_hash": ingestion_result.get("schema_hash"),
            "columns": ingestion_result.get("columns", []),
            "feature_count": feature_count,
            "output_path": ingestion_result.get("output_path"),
        }

    def run_multiple_files(
        self,
        file_paths: List[str],
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest multiple files sequentially.
        """
        results = []
        errors = []

        for fp in file_paths:
            result = self.run_single_file(
                file_path=fp,
                source_type=source_type,
            )
            if result.get("success"):
                results.append(result)
            else:
                errors.append({"file": fp, "error": result.get("error")})

        return {
            "success": len(errors) == 0,
            "total_files": len(file_paths),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    # ──────────────────────────────────────────────
    # Feature store population
    # ──────────────────────────────────────────────

    def _populate_features(
        self,
        run_id: str,
        source_type: str,
        output_path: Optional[str],
    ) -> int:
        """
        Read ingested parquet and convert to long-format features
        for the feature_store table.

        Returns the number of feature records saved.
        """
        if output_path is None:
            logger.warning("No output path for feature population. Skipping.")
            return 0

        parquet_path = Path(output_path)
        if not parquet_path.exists():
            logger.warning(f"Parquet file not found: {parquet_path}")
            return 0

        df = pd.read_parquet(parquet_path)

        if df.empty:
            return 0

        # Convert wide-format DataFrame to long-format feature records
        features = self._dataframe_to_long_features(df, source_type)

        if features:
            feature_store_repo.delete_features_for_run(run_id)
            feature_store_repo.save_features(run_id, features)

        return len(features)

    @staticmethod
    def _dataframe_to_long_features(
        df: pd.DataFrame,
        source_type: str,
    ) -> List[Dict]:
        """
        Convert a wide-format DataFrame into long-format feature records.

        Each numeric column becomes a feature record.
        Each datetime column is used as a timestamp anchor.
        """
        features: List[Dict] = []

        # Identify timestamp column (best-effort)
        timestamp_col = None
        for candidate in ["event_time", "start_date", "report_date", "date",
                          "order_start_time", "aligned_time"]:
            if candidate in df.columns:
                timestamp_col = candidate
                break

        # Identify numeric columns for feature extraction
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        for _, row in df.iterrows():
            ts = None
            if timestamp_col and pd.notna(row.get(timestamp_col)):
                ts_val = row[timestamp_col]
                ts = str(ts_val) if not isinstance(ts_val, str) else ts_val

            for col in numeric_cols:
                val = row.get(col)
                if pd.notna(val):
                    features.append({
                        "feature_name": f"{source_type}__{col}",
                        "feature_value": float(val),
                        "feature_type": "numeric",
                        "timestamp": ts,
                    })

        return features
