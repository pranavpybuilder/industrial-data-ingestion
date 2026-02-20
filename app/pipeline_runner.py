# app/pipeline_runner.py

"""
Pipeline Runner – End-to-end orchestrator for Modules 1-5: Ingestion → Profiling → Rules → ML → Orchestration

Flow:
    1. Create a new analytical run
    2. Ingest the uploaded file (validate, persist parquet)
    3. Save ingestion metadata to DuckDB
    4. Populate feature store (long-format) from ingested data
    5. Profile data (Module 2)
    6. Run ML analysis (Module 4) - PERMANENT & REQUIRED
    7. Apply rules (Module 3)
    8. Orchestrate insights (Module 5) - Merge rule + ML findings
    9. Update run status

Returns unified insights with source tracking (RULE, ML, or MERGED)

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
from storage.repositories.profiling_repo import ProfilingRepository
from storage.repositories.insight_repo import InsightRepository
from ingestion.upload_handler import handle_file_upload
from profiling.column_classifier import ColumnClassifier
from profiling.data_profiler import DataProfiler
from profiling.data_health import compute_data_health
from profiling.equipment_analyzer import EquipmentAnalyzer
from rule_engine.threshold_engine import ThresholdEngine
from rule_engine.maintenance_rules import (
    PMOverdueRule,
    FailurePatternRule,
    TemperatureUptrendRule,
    VibrationSpikeRule,
)
from rule_engine.explainability import RuleExplainer
from ml_engine import MLEngine
from orchestration.insight_orchestrator import InsightOrchestrator
from orchestration.severity_scoring import SeverityScorer
from orchestration.prioritization import InsightPrioritizer
from dashboard_engine.blueprint_generator import BlueprintGenerator
from storage.repositories.dashboard_repo import DashboardRepository
from export.excel_exporter import ExcelExporter
from export.pdf_exporter import PDFExporter
from export.csv_exporter import CSVExporter
from utils.logger import get_logger

logger = get_logger(__name__)

run_repo = RunRepository()
ingestion_repo = IngestionRepository()
feature_store_repo = FeatureStoreRepository()
profiling_repo = ProfilingRepository()
insight_repo = InsightRepository()
dashboard_repo = DashboardRepository()


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

        # ── Step 5: Run profiling (Module 2) ──
        profiling_result = None
        health_score = 0
        try:
            profiling_result = self._profile_data(
                run_id=run_id,
                output_path=ingestion_result.get("output_path"),
            )
            if profiling_result and profiling_result.get("success"):
                health_score = profiling_result.get("health_score", 0)
                logger.info(
                    f"Profiling complete: health_score={health_score:.1f}, "
                    f"{len(profiling_result.get('profiles', []))} columns profiled"
                )
            else:
                logger.warning(
                    f"Profiling returned no results or failed"
                )
        except Exception as exc:
            # Profiling is best-effort, don't fail the run
            logger.warning(
                f"Profiling failed (non-fatal): {exc}"
            )

        # ── Step 5.5: Equipment Analysis (Module 2.5 - Business Intelligence) ──
        equipment_intelligence = {}
        try:
            output_path = ingestion_result.get("output_path")
            if output_path:
                df = pd.read_parquet(output_path)
                
                equipment_analyzer = EquipmentAnalyzer(logger=logger)
                equipment_intelligence = equipment_analyzer.analyze(df)
                
                logger.info(
                    f"Equipment analysis complete: "
                    f"{equipment_intelligence.get('equipment_frequency', {}).get('total_equipment', 0)} equipment, "
                    f"{equipment_intelligence.get('equipment_frequency', {}).get('total_breakdowns', 0)} breakdowns"
                )
        except Exception as exc:
            # Equipment analysis is best-effort
            logger.warning(
                f"Equipment analysis failed (non-fatal): {exc}"
            )

        # ── Step 6: Run ML Engine (Module 4) ──
        ml_findings = []
        try:
            ml_findings = self._run_ml_analysis(
                run_id=run_id,
                output_path=ingestion_result.get("output_path"),
                source_type=resolved_source,
            )
            logger.info(
                f"ML analysis complete: {len(ml_findings)} ML findings generated"
            )
        except Exception as exc:
            # ML is best-effort, don't fail the run
            logger.warning(
                f"ML analysis failed (non-fatal): {exc}"
            )

        # ── Step 7: Apply rules (Module 3) ──
        rule_findings = []
        triggered_rules = 0
        try:
            rule_findings = self._apply_rules(
                run_id=run_id,
                output_path=ingestion_result.get("output_path"),
                profiles=profiling_result.get("profiles", {}) if profiling_result else {},
                source_type=resolved_source,
            )
            triggered_rules = len([r for r in rule_findings if r.get("triggered")])
            logger.info(
                f"Rules applied: {len(rule_findings)} rules checked, "
                f"{triggered_rules} findings triggered"
            )
        except Exception as exc:
            # Rules are best-effort, don't fail the run
            logger.warning(
                f"Rule engine failed (non-fatal): {exc}"
            )

        # ── Step 8: Orchestrate insights (Module 5) ──
        unified_insights = []
        try:
            orchestrator = InsightOrchestrator(logger=logger)
            
            unified_insights = orchestrator.orchestrate(
                run_id=run_id,
                rule_findings=rule_findings,
                ml_findings=ml_findings,
                profiling_results=profiling_result if profiling_result else None,
                equipment_intelligence=equipment_intelligence if equipment_intelligence else None,
            )
            
            # Apply severity scoring
            scorer = SeverityScorer(logger=logger)
            unified_insights = scorer.score_insights(unified_insights)
            
            # Apply prioritization
            prioritizer = InsightPrioritizer(logger=logger)
            unified_insights = prioritizer.prioritize(unified_insights)
            
            logger.info(
                f"Orchestration complete: {len(unified_insights)} unified insights"
            )
        except Exception as exc:
            # Orchestration is best-effort
            logger.warning(
                f"Insight orchestration failed (non-fatal): {exc}"
            )

        # ── Step 8.5: Save insights to repository ──
        try:
            insight_repo.save_insights(run_id=run_id, insights=unified_insights)
            logger.info(f"Insights saved to repository: {len(unified_insights)} insights")
        except Exception as exc:
            logger.warning(f"Failed to save insights to repository (non-fatal): {exc}")

        # ── Step 9: Generate dashboard blueprint (Module 6) ──
        dashboard_blueprint = None
        try:
            blueprint_generator = BlueprintGenerator(logger=logger)
            dashboard_blueprint = blueprint_generator.generate(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result if profiling_result else None,
            )
            dashboard_repo.save_dashboard_blueprint(
                run_id=run_id,
                blueprint=blueprint_generator.to_dict(dashboard_blueprint),
            )
            logger.info(
                f"Dashboard blueprint generated: {len(dashboard_blueprint.sections)} sections"
            )
        except Exception as exc:
            # Dashboard generation is best-effort
            logger.warning(
                f"Dashboard generation failed (non-fatal): {exc}"
            )

        # ── Step 11: Generate exports (Module 7) ──
        export_files = {}
        try:
            # Excel export
            excel_exporter = ExcelExporter(logger=logger)
            excel_report = excel_exporter.export_full_report(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result if profiling_result else None,
            )
            export_files["excel_report"] = excel_report
            
            # PDF export
            pdf_exporter = PDFExporter(logger=logger)
            pdf_report = pdf_exporter.export_comprehensive_report(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result if profiling_result else None,
            )
            export_files["pdf_report"] = pdf_report
            
            # CSV export (batch)
            csv_exporter = CSVExporter(logger=logger)
            csv_files = csv_exporter.export_batch(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result if profiling_result else None,
            )
            export_files.update(csv_files)
            
            logger.info(f"Exports generated: {len(export_files)} files")
        except Exception as exc:
            # Exports are best-effort
            logger.warning(
                f"Export generation failed (non-fatal): {exc}"
            )

        # ── Step 12: Mark run as successful ──
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
            "health_score": health_score,
            "ml_findings_count": len(ml_findings),
            "triggered_rules": triggered_rules,
            "unified_insights_count": len(unified_insights),
            "unified_insights": unified_insights,
            "dashboard_blueprint": dashboard_blueprint.to_dict() if dashboard_blueprint else None,
            "export_files": export_files,
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

    def _profile_data(
        self,
        run_id: str,
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Profile ingested data using Module 2: Profiling Layer
        
        Performs:
        1. Column classification (6 types: numeric, categorical, temporal, etc.)
        2. Statistical profiling (20+ metrics per column)
        3. Health scoring (5 dimensions: completeness, consistency, etc.)
        4. Persists results to profiling_results table
        
        Returns summary of profiling results including health_score.
        """
        if output_path is None:
            logger.warning("No output path for profiling. Skipping.")
            return {"success": False, "error": "No output path"}

        parquet_path = Path(output_path)
        if not parquet_path.exists():
            logger.warning(f"Parquet file not found for profiling: {parquet_path}")
            return {"success": False, "error": "Parquet file not found"}

        try:
            # Read the ingested parquet file
            df = pd.read_parquet(parquet_path)

            if df.empty:
                logger.warning("DataFrame is empty, skipping profiling")
                return {"success": False, "error": "Empty DataFrame"}

            logger.info(f"Profiling data: {df.shape[0]} rows, {df.shape[1]} columns")

            # Step 1: Classify columns
            classifier = ColumnClassifier()
            classifications = classifier.classify(df)
            logger.info(f"Column classification complete: {len(classifications)} columns")

            # Step 2: Profile columns
            profiler = DataProfiler()
            profiles = profiler.profile(df)
            logger.info(f"Data profiling complete: {len(profiles)} column profiles")

            # Step 3: Compute health score
            health_report = compute_data_health(run_id, df)
            overall_health = health_report  # Already computed, returns dict
            health_score = health_report.get("overall_health_score", 0)
            logger.info(f"Health score computed: {health_score:.1f}/100")

            # Step 4: Convert profiles to database format and persist
            profile_records = profiler.profile_to_db_format(df, run_id)
            if profile_records:
                profiling_repo.save_profiling_results(run_id, profile_records)
                logger.info(f"Saved {len(profile_records)} profiling results to DB")

            return {
                "success": True,
                "health_score": health_score,
                "health_details": overall_health,
                "profiles": profiles,
                "profile_records_saved": len(profile_records),
            }

        except Exception as exc:
            logger.error(f"Error during profiling: {exc}", exc_info=True)
            return {
                "success": False,
                "error": str(exc),
            }

    def _run_ml_analysis(
        self,
        run_id: str,
        output_path: Optional[str],
        source_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Run Module 4: ML Engine for anomaly detection, pattern matching, forecasting.
        
        Generates:
        1. Anomaly scores using Isolation Forest
        2. Pattern detections (uptrends, spikes, degradation)
        3. Forecasts with threshold violation alerts
        4. Quality-validated findings
        
        Parameters
        ----------
        run_id : str
            Run ID
        output_path : str, optional
            Path to ingested Parquet file for loading data
        source_type : str
            Data source type (plc, sap, rfid, etc.)
        
        Returns
        -------
        list of ML findings as dicts
        """
        
        # Load dataframe from Parquet output
        df = None
        if output_path:
            try:
                df = pd.read_parquet(output_path)
            except Exception as exc:
                logger.warning(f"Could not load data from {output_path}: {exc}")
        
        if df is None or df.empty:
            logger.warning("No data available for ML analysis. Skipping.")
            return []
        
        try:
            # Load feature store for ML analysis
            features_df = feature_store_repo.get_features_for_run(run_id)
            
            if features_df is None or features_df.empty:
                logger.warning("No features in feature store for ML analysis.")
                return []
            
            logger.info(f"ML analysis starting with {len(features_df)} features")
            
            # Initialize ML engine
            ml_engine = MLEngine(logger=logger)
            
            # Define default safety thresholds (can be enhanced from profiling)
            thresholds = {
                "temperature": 90,
                "pressure": 100,
                "vibration": 5,
                "motor_speed": 3000,
                "flow_rate": 150,
            }
            
            # Execute ML analysis
            ml_findings = ml_engine.execute(features_df, thresholds)
            
            logger.info(f"ML analysis complete: {len(ml_findings)} findings")
            return ml_findings
        
        except Exception as exc:
            logger.error(f"Error during ML analysis: {exc}", exc_info=True)
            return []

    def _apply_rules(
        self,
        run_id: str,
        output_path: Optional[str],
        profiles: Dict[str, Any],
        source_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Apply Module 3: Rules Engine to generate findings.
        
        Evaluates:
        1. Threshold-based rules (numeric bounds, missing data, outliers)
        2. Maintenance-specific rules (PM overdue, failure patterns, etc.)
        
        Parameters
        ----------
        run_id : str
            Run ID
        output_path : str, optional
            Path to ingested Parquet file for loading data
        profiles : dict
            Column profiles from Module 2
        source_type : str
            Data source (plc, sap, rfid, etc.)
        
        Returns
        -------
        list of rule findings as dicts
        """
        
        # Load dataframe from Parquet output
        df = None
        if output_path:
            try:
                df = pd.read_parquet(output_path)
            except Exception as exc:
                logger.warning(f"Could not load data from {output_path}: {exc}")
        
        if df is None or df.empty:
            logger.warning("No data available for rules. Skipping.")
            return []
        
        try:
            # Initialize threshold engine
            threshold_engine = ThresholdEngine()
            
            # Prepare context data
            total_rows = len(df)
            context = {
                "run_id": run_id,
                "source_type": source_type,
                "total_rows": total_rows,
            }
            
            # Apply threshold rules
            threshold_results = []
            if profiles:
                logger.info(f"Applying threshold rules to {len(profiles)} columns")
                
                # Map source-specific key names from configuration
                # For PLC: match temperature, pressure, vibration
                # For SAP: match order dates, failure codes
                source_configs = {
                    "plc": {
                        "temperature": {"min": 0, "max": 90, "critical_max": 100},
                        "pressure": {"min": 0, "max": 10},
                        "vibration": {"min": 0, "max": 5},
                    },
                    "sap": {},
                    "rfid": {},
                    "report_excel": {},
                    "operational_excel": {},
                }
                
                col_config = source_configs.get(source_type, {})
                threshold_results = threshold_engine.apply_to_all_profiles(
                    profiles=profiles,
                    column_configs=col_config,
                    total_rows=total_rows,
                )
            
            # Convert RuleResult objects to dicts
            rule_findings = []
            for result in threshold_results:
                rule_findings.append({
                    "rule_name": result.rule_name,
                    "rule_id": result.rule_id,
                    "triggered": result.triggered,
                    "severity": result.severity,
                    "confidence": result.confidence,
                    "message": result.message,
                    "remediation": result.remediation,
                    "affected_columns": result.affected_columns,
                })
            
            # Apply maintenance-specific rules (if applicable)
            if source_type == "plc":
                logger.info("Applying PLC-specific maintenance rules")
                
                # Temperature uptrend check
                if "temperature" in profiles:
                    temp_rule = TemperatureUptrendRule()
                    result = temp_rule.evaluate({
                        "profile": profiles,
                        "total_rows": total_rows,
                    })
                    if result.triggered:
                        rule_findings.append({
                            "rule_name": result.rule_name,
                            "rule_id": result.rule_id,
                            "triggered": result.triggered,
                            "severity": result.severity,
                            "confidence": result.confidence,
                            "message": result.message,
                            "remediation": result.remediation,
                            "affected_columns": result.affected_columns,
                        })
                
                # Vibration spike check
                if "vibration" in profiles:
                    vib_rule = VibrationSpikeRule()
                    result = vib_rule.evaluate({
                        "profile": profiles,
                        "total_rows": total_rows,
                    })
                    if result.triggered:
                        rule_findings.append({
                            "rule_name": result.rule_name,
                            "rule_id": result.rule_id,
                            "triggered": result.triggered,
                            "severity": result.severity,
                            "confidence": result.confidence,
                            "message": result.message,
                            "remediation": result.remediation,
                            "affected_columns": result.affected_columns,
                        })
            
            elif source_type == "sap":
                logger.info("Applying SAP-specific maintenance rules")
                # PM overdue check would go here
                # Requires PM order data in features
            
            logger.info(f"Rules applied: {len(rule_findings)} findings")
            return rule_findings
        
        except Exception as exc:
            logger.error(f"Error applying rules: {exc}", exc_info=True)
            return []

