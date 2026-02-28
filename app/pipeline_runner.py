"""
Strict end-to-end pipeline orchestration.

Pipeline order:
1. Create run
2. Ingest file
3. Save ingestion metadata
4. Populate feature store
5. Profile data
6. Equipment analysis
7. Rule engine
8. ML engine
9. Insight orchestration
10. Persist insights
11. Generate and persist dashboard blueprint
12. Generate and persist exports
13. Mark run successful
"""

import atexit
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from dashboard_engine.blueprint_generator import BlueprintGenerator
from ingestion.upload_handler import detect_source_type, handle_file_upload
from ingestion.versioning.run_id import generate_run_id
from ml_engine import MLEngine
from orchestration.executive_narrative import ExecutiveNarrativeComposer
from orchestration.insight_orchestrator import InsightOrchestrator
from orchestration.prioritization import InsightPrioritizer
from orchestration.severity_scoring import SeverityScorer
from profiling.column_classifier import ColumnClassifier
from profiling.data_health import compute_data_health
from profiling.data_profiler import DataProfiler
from profiling.equipment_analyzer import EquipmentAnalyzer
from rule_engine.explainability import RuleExplainer
from rule_engine.maintenance_rules import (
    FailurePatternRule,
    PMOverdueRule,
    TemperatureUptrendRule,
    VibrationSpikeRule,
)
from rule_engine.threshold_engine import ThresholdEngine
from storage.connection import close_connection, initialize_database
from storage.repositories.dashboard_repo import DashboardRepository
from storage.repositories.export_repo import ExportRepository
from storage.repositories.feature_store_repo import FeatureStoreRepository
from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.insight_repo import InsightRepository
from storage.repositories.profiling_repo import ProfilingRepository
from storage.repositories.run_repo import RunRepository, RunStatus
from utils.logger import get_logger

logger = get_logger(__name__)

run_repo = RunRepository()
ingestion_repo = IngestionRepository()
feature_store_repo = FeatureStoreRepository()
profiling_repo = ProfilingRepository()
insight_repo = InsightRepository()
dashboard_repo = DashboardRepository()
export_repo = ExportRepository()


class PipelineRunner:
    def __init__(self) -> None:
        initialize_database()
        # ── Register DB close on process exit ─────────────────────────────────
        # This ensures the DuckDB file lock is ALWAYS released cleanly,
        # even on crash, so the next launch never hits "file in use" error.
        atexit.register(close_connection)
        logger.info("Pipeline runner initialized. Database ready.")

    def run_single_file(
        self,
        file_path: str,
        source_type: Optional[str] = None,
        run_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        current_step = "resolve_source"
        run_id: Optional[str] = None

        try:
            resolved_source = (
                source_type
                or detect_source_type(file_path)
                or "generic_tabular"
            )
            resolved_source = resolved_source.lower().strip()

            file_name = Path(file_path).name
            run_id = generate_run_id()
            run_name = run_name or f"{resolved_source}_{file_name}"

            current_step = "create_run"
            run_repo.create_run(
                run_id=run_id,
                run_name=run_name,
                source_type=resolved_source,
                status=RunStatus.PENDING,
            )
            run_repo.update_status(run_id, RunStatus.RUNNING)

            current_step = "ingest_file"
            ingestion_result = handle_file_upload(
                file_path=file_path,
                source_type=resolved_source,
                run_id=run_id,
            )
            if not ingestion_result.get("success"):
                raise RuntimeError(
                    ingestion_result.get("error", "Ingestion failed")
                )

            output_path = ingestion_result.get("output_path")
            if not output_path:
                raise RuntimeError("Ingestion output_path is missing")

            current_step = "persist_ingestion"
            file_id = str(uuid.uuid4())[:12]
            current_schema_hash = ingestion_result.get("schema_hash")
            current_schema_type = ingestion_result.get("source_schema_type")
            previous_schema_hash = ingestion_repo.get_latest_schema_hash_for_source(
                source_type=resolved_source,
                source_schema_type=current_schema_type,
            )
            schema_drift_detected = bool(
                previous_schema_hash
                and current_schema_hash
                and previous_schema_hash != current_schema_hash
            )

            ingestion_repo.save_ingested_file(
                file_id=file_id,
                run_id=run_id,
                file_name=ingestion_result.get("file_name", file_name),
                source_type=resolved_source,
                source_schema_type=current_schema_type,
                schema_version=ingestion_result.get("schema_version"),
                schema_hash=current_schema_hash,
                schema_drift_detected=schema_drift_detected,
                original_column_snapshot=ingestion_result.get(
                    "original_column_snapshot", []
                ),
                normalized_column_snapshot=ingestion_result.get(
                    "normalized_column_snapshot", []
                ),
                column_mapping=ingestion_result.get("column_mapping", {}),
                mapping_decisions=ingestion_result.get("mapping_decisions", []),
                unmapped_source_columns=ingestion_result.get(
                    "unmapped_source_columns", []
                ),
                row_count=int(ingestion_result.get("rows", 0)),
                output_path=output_path,
            )

            current_step = "feature_store"
            feature_count = self._populate_features(
                run_id=run_id,
                source_type=resolved_source,
                output_path=output_path,
            )
            if feature_count <= 0:
                raise RuntimeError("No features were generated for this run")

            current_step = "profiling"
            profiling_result = self._profile_data(
                run_id=run_id,
                output_path=output_path,
            )
            if not profiling_result.get("success"):
                raise RuntimeError(
                    profiling_result.get("error", "Profiling failed")
                )

            current_step = "equipment_analysis"
            equipment_intelligence = self._run_equipment_analysis(output_path)

            current_step = "rule_engine"
            rule_findings = self._apply_rules(
                run_id=run_id,
                output_path=output_path,
                profiles=profiling_result.get("profiles", {}),
                source_type=resolved_source,
            )

            current_step = "ml_engine"
            ml_findings = self._run_ml_analysis(
                run_id=run_id,
                output_path=output_path,
                source_type=resolved_source,
            )

            current_step = "orchestration"
            orchestrator = InsightOrchestrator(logger=logger)
            unified_insights = orchestrator.orchestrate(
                run_id=run_id,
                rule_findings=rule_findings,
                ml_findings=ml_findings,
                profiling_results=profiling_result.get("profiles", {}),
                equipment_intelligence=equipment_intelligence,
            )

            scorer = SeverityScorer(logger=logger)
            unified_insights = scorer.score_insights(unified_insights)
            prioritizer = InsightPrioritizer(logger=logger)
            unified_insights = prioritizer.prioritize(unified_insights)

            if not unified_insights:
                unified_insights = [
                    {
                        "insight_id": str(uuid.uuid4())[:12],
                        "run_id": run_id,
                        "source": "SYSTEM",
                        "severity": "INFO",
                        "resource": "SYSTEM",
                        "title": "No anomalies detected",
                        "description": "Pipeline completed with no rule or ML alerts.",
                        "remediation": "No action required.",
                        "priority_score": 0.2,
                        "priority_rank": 1,
                        "priority_tier": "LOW",
                        "needs_action": False,
                        "action_type": "MONITOR",
                    }
                ]

            current_step = "executive_narrative"
            narrative_composer = ExecutiveNarrativeComposer()
            narrative_payload = narrative_composer.compose(
                run_id=run_id,
                source_type=resolved_source,
                raw_df=pd.read_parquet(output_path),
                unified_insights=unified_insights,
                rule_findings=rule_findings,
                ml_findings=ml_findings,
                profiling_result=profiling_result,
            )
            narrative_insight = narrative_composer.build_narrative_insight(
                run_id=run_id,
                narrative=narrative_payload,
            )
            unified_insights.append(narrative_insight)
            unified_insights = sorted(
                unified_insights,
                key=lambda insight: float(insight.get("priority_score", 0.0)),
                reverse=True,
            )
            for rank, insight in enumerate(unified_insights, start=1):
                insight["priority_rank"] = rank

            current_step = "persist_insights"
            insight_repo.save_insights(run_id=run_id, insights=unified_insights)

            current_step = "dashboard_blueprint"
            blueprint_generator = BlueprintGenerator(logger=logger)
            dashboard_blueprint = blueprint_generator.generate(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result.get("profiles", {}),
            )
            if not blueprint_generator.validate_blueprint(dashboard_blueprint):
                raise RuntimeError("Generated dashboard blueprint is invalid")

            dashboard_repo.save_dashboard_blueprint(
                run_id=run_id,
                blueprint=blueprint_generator.to_dict(dashboard_blueprint),
            )

            current_step = "exports"
            export_files = self._generate_exports(
                run_id=run_id,
                unified_insights=unified_insights,
                profiling_results=profiling_result,
            )
            self._persist_exports(run_id, export_files)

            current_step = "mark_success"
            run_repo.update_status(run_id, RunStatus.SUCCESS)

            return {
                "success": True,
                "run_id": run_id,
                "file_name": ingestion_result.get("file_name", file_name),
                "source_type": resolved_source,
                "rows": int(ingestion_result.get("rows", 0)),
                "schema_hash": ingestion_result.get("schema_hash"),
                "schema_version": ingestion_result.get("schema_version"),
                "source_schema_type": ingestion_result.get("source_schema_type"),
                "schema_drift_detected": schema_drift_detected,
                "column_mapping": ingestion_result.get("column_mapping", {}),
                "columns": ingestion_result.get("columns", []),
                "feature_count": feature_count,
                "health_score": profiling_result.get("health_score", 0),
                "rule_findings_count": len(rule_findings),
                "ml_findings_count": len(ml_findings),
                "unified_insights_count": len(unified_insights),
                "unified_insights": unified_insights,
                "executive_narrative": narrative_payload,
                "dashboard_blueprint": blueprint_generator.to_dict(dashboard_blueprint),
                "export_files": export_files,
                "output_path": output_path,
            }

        except Exception as exc:
            if run_id:
                try:
                    run_repo.mark_failed(
                        run_id=run_id,
                        error_message=str(exc),
                        failed_step=current_step,
                    )
                except Exception as status_exc:
                    logger.error(
                        "Failed to mark run %s as FAILED: %s",
                        run_id,
                        status_exc,
                    )

            logger.error(
                "Pipeline failed at step '%s' for file '%s': %s",
                current_step,
                file_path,
                exc,
                exc_info=True,
            )
            return {
                "success": False,
                "run_id": run_id,
                "failed_step": current_step,
                "error": str(exc),
            }

    def run_multiple_files(
        self,
        file_paths: List[str],
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for fp in file_paths:
            result = self.run_single_file(file_path=fp, source_type=source_type)
            if result.get("success"):
                results.append(result)
            else:
                errors.append(
                    {
                        "file": fp,
                        "run_id": result.get("run_id"),
                        "failed_step": result.get("failed_step"),
                        "error": result.get("error"),
                    }
                )

        return {
            "success": len(errors) == 0,
            "total_files": len(file_paths),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    def _populate_features(
        self,
        run_id: str,
        source_type: str,
        output_path: str,
    ) -> int:
        parquet_path = Path(output_path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

        df = pd.read_parquet(parquet_path)
        if df.empty:
            raise ValueError("Ingested parquet is empty")

        features = self._extract_source_features(df, source_type)
        if not features:
            return 0

        feature_store_repo.delete_features_for_run(run_id)
        feature_store_repo.save_features(run_id, features)
        return len(features)

    def _extract_source_features(
        self,
        df: pd.DataFrame,
        source_type: str,
    ) -> List[Dict[str, Any]]:
        normalized_source = str(source_type or "").strip().lower()

        if normalized_source in {"sap", "report_excel"}:
            features = self._extract_sap_features(df)
        elif normalized_source == "maintenance":
            features = self._extract_maintenance_features(df)
        elif normalized_source == "energy":
            features = self._extract_energy_features(df)
        elif normalized_source == "rfid":
            features = self._extract_rfid_features(df)
        elif normalized_source == "plc":
            features = self._extract_plc_features(df)
        else:
            # For generic_tabular and unknown sources:
            # Try maintenance detection first (if columns suggest it)
            maint_cols = {"breakdown_dur", "equipment", "malfunct_start", "breakdown"}
            if maint_cols.intersection(set(df.columns)):
                features = self._extract_maintenance_features(df)
            else:
                features = self._extract_generic_features(
                    df, prefix=normalized_source or "generic"
                )

        if features:
            return features

        # Loud fallback path for unexpectedly sparse schemas.
        fallback = self._extract_generic_features(df, prefix="generic")
        if fallback:
            logger.warning(
                "Source-specific feature extraction produced no rows for '%s'. "
                "Using generic numeric feature extraction.",
                source_type,
            )
        return fallback

    @staticmethod
    def _extract_sap_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)
        breakdown = pd.to_numeric(
            df.get("breakdown_count", pd.Series([1] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(1.0)
        downtime = pd.to_numeric(
            df.get("downtime_hours", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)

        feature_frame = pd.DataFrame(
            {
                "ts": timestamps,
                "breakdown_count": breakdown,
                "downtime_hours": downtime,
            }
        )

        for row in feature_frame.itertuples(index=False):
            ts = PipelineRunner._as_timestamp(row.ts)
            PipelineRunner._append_feature(
                features, "sap__breakdown_count", row.breakdown_count, ts
            )
            PipelineRunner._append_feature(
                features, "sap__downtime_hours", row.downtime_hours, ts
            )

        daily = (
            feature_frame.dropna(subset=["ts"])
            .set_index("ts")
            .resample("D")
            .sum(numeric_only=True)
        )
        for ts, row in daily.iterrows():
            iso_ts = PipelineRunner._as_timestamp(ts)
            PipelineRunner._append_feature(
                features,
                "sap_daily__breakdown_count",
                row.get("breakdown_count", 0.0),
                iso_ts,
            )
            PipelineRunner._append_feature(
                features,
                "sap_daily__downtime_hours",
                row.get("downtime_hours", 0.0),
                iso_ts,
            )

        return features

    @staticmethod
    def _extract_maintenance_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract features from maintenance/breakdown datasets.

        Handles Breakdown_data.csv columns:
        - breakdown_dur: float — breakdown duration in minutes/hours
        - equipment: int — equipment ID
        - notification: int — notification number
        - why1..why_5: text — 5-Why root cause chain
        - due_to_1..due_to_5: text — due-to chain
        - malfunct_start, created_on: datetime — timestamps
        - breakdown: text — breakdown indicator
        - coding_code_txt: text — failure coding
        """
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)

        # ── Feature 1: Breakdown duration (numeric) ──
        breakdown_dur = pd.to_numeric(
            df.get("breakdown_dur", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)

        for idx in range(len(df)):
            ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
            PipelineRunner._append_feature(
                features, "maint__breakdown_duration", breakdown_dur.iloc[idx], ts
            )

        # ── Feature 2: Breakdown count (1 per row) ──
        for idx in range(len(df)):
            ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
            PipelineRunner._append_feature(
                features, "maint__breakdown_count", 1.0, ts
            )

        # ── Feature 3: 5-Why completion score per row ──
        # Score = (number of non-null why fields) / 5
        why_cols = [c for c in df.columns if c.startswith("why") and c != "why_why_done_by"]
        if why_cols:
            for idx in range(len(df)):
                ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
                filled = sum(
                    1 for c in why_cols
                    if pd.notna(df[c].iloc[idx]) and str(df[c].iloc[idx]).strip() != ""
                )
                score = filled / max(len(why_cols), 1)
                PipelineRunner._append_feature(
                    features, "maint__why_completion_score", score, ts
                )

        # ── Feature 4: Due-to chain completion ──
        due_to_cols = [c for c in df.columns if c.startswith("due_to")]
        if due_to_cols:
            for idx in range(len(df)):
                ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
                filled = sum(
                    1 for c in due_to_cols
                    if pd.notna(df[c].iloc[idx]) and str(df[c].iloc[idx]).strip() != ""
                )
                score = filled / max(len(due_to_cols), 1)
                PipelineRunner._append_feature(
                    features, "maint__due_to_completion_score", score, ts
                )

        # ── Feature 5: Equipment breakdown counts (per equipment) ──
        if "equipment" in df.columns:
            equipment_ids = pd.to_numeric(df["equipment"], errors="coerce")
            for idx in range(len(df)):
                ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
                eq_id = equipment_ids.iloc[idx]
                if pd.notna(eq_id):
                    PipelineRunner._append_feature(
                        features, f"maint__equip_{int(eq_id)}_breakdown", 1.0, ts
                    )

        # ── Feature 6: Daily aggregates ──
        if timestamps.notna().any():
            daily_frame = pd.DataFrame({
                "ts": timestamps,
                "breakdown_dur": breakdown_dur,
                "count": 1,
            }).dropna(subset=["ts"])

            if not daily_frame.empty:
                daily = daily_frame.set_index("ts").resample("D").agg({
                    "breakdown_dur": "sum",
                    "count": "sum",
                })
                for ts_val, row in daily.iterrows():
                    iso_ts = PipelineRunner._as_timestamp(ts_val)
                    PipelineRunner._append_feature(
                        features,
                        "maint_daily__breakdown_duration",
                        row.get("breakdown_dur", 0.0),
                        iso_ts,
                    )
                    PipelineRunner._append_feature(
                        features,
                        "maint_daily__breakdown_count",
                        row.get("count", 0.0),
                        iso_ts,
                    )

        # ── Feature 7: All remaining numeric columns as generic features ──
        numeric_cols = sorted(
            c for c in df.select_dtypes(include=["number"]).columns
            if c not in {"breakdown_dur"}
        )
        for idx in range(len(df)):
            ts = PipelineRunner._as_timestamp(timestamps.iloc[idx])
            for col in numeric_cols:
                PipelineRunner._append_feature(
                    features,
                    f"maint__{col}",
                    df[col].iloc[idx],
                    ts,
                )

        return features

    @staticmethod
    def _extract_energy_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)
        energy = pd.to_numeric(
            df.get("energy_kwh", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)
        production = pd.to_numeric(
            df.get("production_units", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)
        cost = pd.to_numeric(
            df.get("energy_cost", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)
        intensity = energy / production.replace(0, pd.NA)
        intensity = intensity.replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)

        for ts, kwh, units, value_cost, metric_intensity in zip(
            timestamps,
            energy,
            production,
            cost,
            intensity,
        ):
            iso_ts = PipelineRunner._as_timestamp(ts)
            PipelineRunner._append_feature(features, "energy__kwh", kwh, iso_ts)
            PipelineRunner._append_feature(
                features, "energy__production_units", units, iso_ts
            )
            PipelineRunner._append_feature(features, "energy__cost", value_cost, iso_ts)
            PipelineRunner._append_feature(
                features, "energy__kwh_per_unit", metric_intensity, iso_ts
            )

        return features

    @staticmethod
    def _extract_rfid_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)
        signal_strength = pd.to_numeric(
            df.get("signal_strength", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)

        for ts, strength in zip(timestamps, signal_strength):
            iso_ts = PipelineRunner._as_timestamp(ts)
            PipelineRunner._append_feature(features, "rfid__event_count", 1.0, iso_ts)
            PipelineRunner._append_feature(
                features, "rfid__signal_strength", strength, iso_ts
            )

        hourly = (
            pd.DataFrame({"ts": timestamps, "event_count": 1})
            .dropna(subset=["ts"])
            .set_index("ts")
            .resample("H")
            .sum(numeric_only=True)
        )
        for ts, row in hourly.iterrows():
            PipelineRunner._append_feature(
                features,
                "rfid_hourly__event_count",
                row.get("event_count", 0.0),
                PipelineRunner._as_timestamp(ts),
            )

        return features

    @staticmethod
    def _extract_plc_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)
        parameter_name = (
            df.get(
                "parameter_name",
                pd.Series(["unknown"] * len(df), index=df.index),
            )
            .astype("string")
            .fillna("unknown")
            .str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9_]+", "_", regex=True)
            .replace("", "unknown")
        )
        parameter_value = pd.to_numeric(
            df.get("parameter_value", pd.Series([0.0] * len(df), index=df.index)),
            errors="coerce",
        ).fillna(0.0)

        for ts, pname, pvalue in zip(timestamps, parameter_name, parameter_value):
            iso_ts = PipelineRunner._as_timestamp(ts)
            PipelineRunner._append_feature(
                features,
                f"plc__{pname}_value",
                pvalue,
                iso_ts,
            )

        return features

    @staticmethod
    def _extract_generic_features(
        df: pd.DataFrame,
        prefix: str,
    ) -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if df.empty:
            return features

        timestamps = PipelineRunner._resolve_timestamps(df)
        numeric_cols = sorted(df.select_dtypes(include=["number"]).columns.tolist())

        for index, row in df.reset_index(drop=True).iterrows():
            ts = PipelineRunner._as_timestamp(timestamps.iloc[index])
            for column in numeric_cols:
                PipelineRunner._append_feature(
                    features,
                    f"{prefix}__{column}",
                    row.get(column),
                    ts,
                )

        return features

    @staticmethod
    def _resolve_timestamps(df: pd.DataFrame) -> pd.Series:
        """Resolve the best timestamp column from the DataFrame."""
        for candidate in [
            "event_time",
            "created_on",
            "start_date",
            "malfunct_start",
            "report_date",
            "date",
            "timestamp",
            "changed_on",
            "malfunct_end",
            "malfunction_end",
            "mal_start_t",
            "order_date",
            "aligned_time",
        ]:
            if candidate not in df.columns:
                continue
            parsed = pd.to_datetime(df[candidate], errors="coerce", utc=True)
            if parsed.notna().sum() > 0:
                return parsed

        # Fallback: find any column with 'date' or 'time' in the name
        for col in df.columns:
            col_lower = str(col).lower()
            if any(token in col_lower for token in ("date", "time")):
                parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
                if parsed.notna().sum() > 0:
                    return parsed

        return pd.Series([pd.NaT] * len(df), index=df.index)

    @staticmethod
    def _as_timestamp(value: Any) -> Optional[str]:
        if pd.isna(value):
            return None
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            return None
        return parsed.isoformat()

    @staticmethod
    def _append_feature(
        target: List[Dict[str, Any]],
        feature_name: str,
        value: Any,
        timestamp: Optional[str],
        feature_type: str = "numeric",
    ) -> None:
        numeric = pd.to_numeric(value, errors="coerce")
        if pd.isna(numeric):
            return
        target.append(
            {
                "feature_name": feature_name,
                "feature_value": float(numeric),
                "feature_type": feature_type,
                "timestamp": timestamp,
            }
        )

    def _profile_data(
        self,
        run_id: str,
        output_path: str,
    ) -> Dict[str, Any]:
        parquet_path = Path(output_path)
        if not parquet_path.exists():
            return {"success": False, "error": f"File not found: {parquet_path}"}

        df = pd.read_parquet(parquet_path)
        if df.empty:
            return {"success": False, "error": "DataFrame is empty"}

        classifier = ColumnClassifier()
        _ = classifier.classify(df)

        profiler = DataProfiler()
        profiles = profiler.profile(df)

        health_report = compute_data_health(run_id, df)
        health_score = float(health_report.get("overall_health_score", 0))

        profile_records = profiler.profile_to_db_format(df, run_id)
        profiling_repo.save_profiling_results(run_id, profile_records)

        return {
            "success": True,
            "health_score": health_score,
            "health_details": health_report,
            "profiles": profiles,
            "profile_records_saved": len(profile_records),
        }

    def _run_equipment_analysis(self, output_path: str) -> Dict[str, Any]:
        df = pd.read_parquet(output_path)
        if df.empty:
            raise ValueError("No rows available for equipment analysis")

        analyzer = EquipmentAnalyzer(logger=logger)
        return analyzer.analyze(df)

    def _run_ml_analysis(
        self,
        run_id: str,
        output_path: str,
        source_type: str,
    ) -> List[Dict[str, Any]]:
        raw_df = pd.read_parquet(output_path)
        features_df = feature_store_repo.get_features_for_run(run_id)

        if features_df is None or features_df.empty:
            raise ValueError("No features available for ML analysis")

        engine = MLEngine(logger=logger)
        findings = engine.execute(
            features_df=features_df,
            source_type=source_type,
            run_id=run_id,
            raw_df=raw_df,
        )

        if findings is None:
            return []
        return findings

    def _apply_rules(
        self,
        run_id: str,
        output_path: str,
        profiles: Dict[str, Any],
        source_type: str,
    ) -> List[Dict[str, Any]]:
        df = pd.read_parquet(output_path)
        if df.empty:
            raise ValueError("No rows available for rule evaluation")

        threshold_engine = ThresholdEngine()
        total_rows = len(df)

        source_configs: Dict[str, Dict[str, Dict[str, float]]] = {
            "plc": {
                "temperature": {"min": 0, "max": 90, "critical_max": 100},
                "pressure": {"min": 0, "max": 10},
                "vibration": {"min": 0, "max": 5},
            },
            "sap": {},
            "rfid": {},
            "energy": {},
            "report_excel": {},
            "operational_excel": {},
            "generic_tabular": {},
        }

        # Auto-map generic numeric columns for threshold monitoring.
        if source_type == "generic_tabular":
            for column_name, profile in profiles.items():
                if profile.get("detected_type") != "numeric":
                    continue
                col = column_name.lower()
                if "temperature" in col:
                    source_configs["generic_tabular"][column_name] = {"max": 90}
                elif "pressure" in col:
                    source_configs["generic_tabular"][column_name] = {"max": 10}
                elif "vibration" in col:
                    source_configs["generic_tabular"][column_name] = {"max": 5}
                elif "downtime" in col:
                    source_configs["generic_tabular"][column_name] = {"max": 240}

        threshold_results = threshold_engine.apply_to_all_profiles(
            profiles=profiles,
            column_configs=source_configs.get(source_type, {}),
            total_rows=total_rows,
        )

        rule_findings: List[Dict[str, Any]] = []
        for result in threshold_results:
            rule_findings.append(
                {
                    "rule_name": result.rule_name,
                    "rule_id": result.rule_id,
                    "triggered": result.triggered,
                    "severity": str(result.severity).upper(),
                    "confidence": float(result.confidence),
                    "message": result.message,
                    "remediation": result.remediation,
                    "affected_columns": result.affected_columns,
                }
            )

        # Source-aware maintenance heuristics.
        context = {"profile": profiles, "total_rows": total_rows}
        if "temperature" in profiles:
            result = TemperatureUptrendRule().evaluate(context)
            rule_findings.append(
                {
                    "rule_name": result.rule_name,
                    "rule_id": result.rule_id,
                    "triggered": result.triggered,
                    "severity": str(result.severity).upper(),
                    "confidence": float(result.confidence),
                    "message": result.message,
                    "remediation": result.remediation,
                    "affected_columns": result.affected_columns,
                }
            )

        if "vibration" in profiles:
            result = VibrationSpikeRule().evaluate(context)
            rule_findings.append(
                {
                    "rule_name": result.rule_name,
                    "rule_id": result.rule_id,
                    "triggered": result.triggered,
                    "severity": str(result.severity).upper(),
                    "confidence": float(result.confidence),
                    "message": result.message,
                    "remediation": result.remediation,
                    "affected_columns": result.affected_columns,
                }
            )

        # SAP-oriented rules can still run opportunistically when features exist.
        feature_records = feature_store_repo.get_features_for_run(run_id)
        feature_context = {"features": feature_records.to_dict("records")}
        if source_type == "sap":
            for rule in (PMOverdueRule(), FailurePatternRule()):
                result = rule.evaluate(feature_context)
                rule_findings.append(
                    {
                        "rule_name": result.rule_name,
                        "rule_id": result.rule_id,
                        "triggered": result.triggered,
                        "severity": str(result.severity).upper(),
                        "confidence": float(result.confidence),
                        "message": result.message,
                        "remediation": result.remediation,
                        "affected_columns": result.affected_columns,
                    }
                )

        # Attach explainability for triggered findings.
        explainer = RuleExplainer()
        for finding in rule_findings:
            if not finding.get("triggered"):
                continue
            explanation = explainer.explain_result(
                type(
                    "_RuleLike",
                    (),
                    {
                        "rule_name": finding["rule_name"],
                        "severity": finding["severity"].lower(),
                        "triggered": finding["triggered"],
                        "confidence": finding["confidence"],
                        "message": finding["message"],
                        "remediation": finding["remediation"],
                        "affected_columns": finding["affected_columns"],
                        "data": {},
                    },
                )()
            )
            finding["explanation"] = explanation

        return rule_findings

    def _generate_exports(
        self,
        run_id: str,
        unified_insights: List[Dict[str, Any]],
        profiling_results: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        try:
            from export.excel_exporter import ExcelExporter
            from export.pdf_exporter import PDFExporter
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Missing export dependency: {exc.name}. "
                "Install project requirements before running exports."
            ) from exc

        export_files: Dict[str, Any] = {}
        export_profiling_payload = self._build_export_profiling_payload(
            profiling_results
        )

        excel_exporter = ExcelExporter(logger=logger)
        export_files["excel_report"] = excel_exporter.export_full_report(
            run_id=run_id,
            unified_insights=unified_insights,
            profiling_results=export_profiling_payload,
        )

        pdf_exporter = PDFExporter()
        export_files["pdf_report"] = pdf_exporter.export_insights_pdf(
            run_id=run_id,
            unified_insights=unified_insights,
            profiling_results=export_profiling_payload,
        )

        return export_files

    def _persist_exports(self, run_id: str, export_files: Dict[str, Any]) -> None:
        def _save(path: str, export_type: str, scope: str) -> None:
            export_repo.save_export(
                export_id=str(uuid.uuid4())[:12],
                run_id=run_id,
                export_type=export_type,
                scope=scope,
                file_path=path,
            )

        for key, value in export_files.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if nested_value:
                        _save(str(nested_value), nested_key, key)
                continue

            if value:
                _save(str(value), key, key)

    @staticmethod
    def _build_export_profiling_payload(
        profiling_results: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not profiling_results:
            return None

        profiles = profiling_results.get("profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}

        columns: Dict[str, Dict[str, Any]] = {}
        for column_name, profile in profiles.items():
            if not isinstance(profile, dict):
                continue

            null_pct = float(profile.get("null_percentage", 0.0))
            columns[column_name] = {
                "type": profile.get("detected_type", "unknown"),
                "non_null_percentage": max(0.0, 100.0 - null_pct),
                "unique_values": int(profile.get("unique_count", 0)),
                "missing_count": int(profile.get("null_count", 0)),
                "missing_percentage": null_pct,
                "mean": profile.get("mean"),
                "median": profile.get("median"),
                "std_dev": profile.get("std"),
                "min": profile.get("min"),
                "max": profile.get("max"),
                "distinct_count": int(profile.get("unique_count", 0)),
            }

        health_details = profiling_results.get("health_details", {})
        quality_issues = health_details.get("column_issues", [])
        formatted_issues = []
        for issue in quality_issues:
            if not isinstance(issue, dict):
                continue
            formatted_issues.append(
                {
                    "column": issue.get("column_name", ""),
                    "issue_type": issue.get("message", ""),
                    "severity": issue.get("severity", ""),
                    "details": issue.get("message", ""),
                }
            )

        return {
            "columns": columns,
            "quality_metrics": {
                "health_score": float(profiling_results.get("health_score", 0.0)),
                "total_missing": int(
                    sum(int(v.get("missing_count", 0)) for v in columns.values())
                ),
                "issues": formatted_issues,
            },
        }