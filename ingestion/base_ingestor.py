from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Any, Dict, List, Optional
import pandas as pd

from schema_registry.column_mapper import ColumnMapper, ColumnMappingError
from schema_registry.schema_registry import SchemaRegistry, SchemaRegistryError

from .versioning.run_id import generate_run_id
from .versioning.data_versioner import DataVersioner
from .validators.schema_validator import SchemaValidator
from .validators.type_validator import TypeValidator
from .validators.time_validator import TimeValidator


class BaseIngestor(ABC):
    """
    Base class for all data ingestors.

    Enforces a strict, production-grade ingestion lifecycle:
    1. Read raw data
    2. Validate schema, types, and time columns
    3. Version the dataset
    4. Persist data to raw storage
    5. Return metadata for downstream layers
    """

    def __init__(
        self,
        source_name: str,
        source_path: str,
        schema_path: Optional[str],
        output_dir: str,
        run_id: Optional[str] = None,
        schema_type: Optional[str] = None,
    ):
        self.source_name = source_name
        self.source_path = Path(source_path)
        self.schema_path = Path(schema_path) if schema_path else None
        self.output_dir = Path(output_dir)
        self.schema_type = schema_type

        self.run_id = run_id or generate_run_id()
        self.ingestion_time = datetime.utcnow()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.versioner = DataVersioner(self.output_dir)
        self.schema_registry = SchemaRegistry()
        self.column_mapper = ColumnMapper()

    # ------------------------------------------------------------------
    # Mandatory methods to be implemented by child ingestors
    # ------------------------------------------------------------------

    @abstractmethod
    def read(self) -> pd.DataFrame:
        """
        Read raw data from the source.
        Must return a pandas DataFrame.
        """
        pass

    # ------------------------------------------------------------------
    # Core ingestion pipeline (DO NOT OVERRIDE)
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        """
        Execute the full ingestion pipeline.
        This method must never be overridden.
        """
        data = self.read()
        self._validate_not_empty(data)
        return self.ingest_dataframe(
            data=self.preprocess(data),
            original_column_snapshot=list(data.columns),
        )

    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optional source-specific preprocessing hook.
        Subclasses may override when needed.
        """
        return data

    def ingest_dataframe(
        self,
        data: pd.DataFrame,
        original_column_snapshot: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute ingestion from an already loaded/preprocessed DataFrame.
        """
        self._validate_not_empty(data)

        working = data.copy()
        mapping_report: Optional[Dict[str, Any]] = None
        schema_version: Optional[str] = None

        if self.schema_type:
            try:
                schema = self.schema_registry.load_schema(self.schema_type)
                schema_version = str(schema.get("schema_version", "unknown"))
                working, mapping_report = self.column_mapper.map_dataframe(
                    df=working,
                    schema=schema,
                    source_type=self.schema_type,
                )
            except (SchemaRegistryError, ColumnMappingError) as exc:
                raise ValueError(
                    f"[{self.source_name}] Canonical mapping failed: {exc}"
                ) from exc

            detected_time_column = self._resolve_time_column(working)
            if detected_time_column:
                self._validate_no_future_time(working, detected_time_column)
        else:
            self._validate_schema(working)
            self._validate_types(working)
            self._validate_time(working)

        self._validate_not_empty(working)
        versioned_path = self._persist(working)

        return self._build_metadata(
            path=versioned_path,
            data=working,
            schema_version=schema_version,
            mapping_report=mapping_report,
            original_column_snapshot=(
                [str(c) for c in original_column_snapshot]
                if original_column_snapshot is not None
                else [str(c) for c in data.columns]
            ),
        )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_not_empty(self, data: pd.DataFrame):
        if data is None or data.empty:
            raise ValueError(
                f"[{self.source_name}] Ingestion failed: dataset is empty"
            )

    def _validate_schema(self, data: pd.DataFrame):
        if self.schema_path is None:
            return
        SchemaValidator.validate(data, self.schema_path)

    def _validate_types(self, data: pd.DataFrame):
        if self.schema_path is None:
            return
        TypeValidator.validate(data, self.schema_path)

    def _validate_time(self, data: pd.DataFrame):
        if self.schema_path is None:
            return
        TimeValidator.validate(data, self.schema_path)

    @staticmethod
    def _resolve_time_column(data: pd.DataFrame) -> Optional[str]:
        for candidate in [
            "event_time",
            "start_date",
            "date",
            "report_date",
            "timestamp",
            "created_on",
        ]:
            if candidate in data.columns:
                return candidate
        return None

    @staticmethod
    def _validate_no_future_time(data: pd.DataFrame, column: str) -> None:
        now_utc = pd.Timestamp.utcnow()
        series = pd.to_datetime(data[column], errors="coerce", utc=True)
        future_count = int((series > now_utc).sum())
        if future_count > 0:
            raise ValueError(
                f"Time validation failed: {future_count} future timestamps in '{column}'"
            )

    # ------------------------------------------------------------------
    # Persistence & versioning
    # ------------------------------------------------------------------

    def _persist(self, data: pd.DataFrame) -> Path:
        """
        Persist data using versioning.
        Output format is Parquet for ML efficiency.
        """
        filename = f"{self.source_name}.parquet"
        return self.versioner.save(
            data=data,
            filename=filename,
            run_id=self.run_id,
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _generate_schema_hash(self, data: pd.DataFrame) -> str:
        """
        Generate a deterministic hash of the column structure
        (names + dtypes) for schema change detection.
        """
        schema_signature = "|".join(
            f"{col}:{dtype}" for col, dtype in
            sorted(zip(data.columns, data.dtypes.astype(str)))
        )
        return hashlib.sha256(schema_signature.encode("utf-8")).hexdigest()[:16]

    def _build_metadata(
        self,
        path: Path,
        data: pd.DataFrame,
        schema_version: Optional[str] = None,
        mapping_report: Optional[Dict[str, Any]] = None,
        original_column_snapshot: Optional[List[str]] = None,
    ) -> dict:
        """
        Metadata returned to orchestration layer.
        """
        metadata = {
            "source": self.source_name,
            "run_id": self.run_id,
            "file_name": self.source_path.name,
            "rows": len(data),
            "columns": list(data.columns),
            "schema_hash": self._generate_schema_hash(data),
            "output_path": str(path),
            "ingested_at": self.ingestion_time.isoformat(),
        }

        if self.schema_type:
            metadata["source_schema_type"] = self.schema_type
        if schema_version:
            metadata["schema_version"] = schema_version
        if original_column_snapshot is not None:
            metadata["original_column_snapshot"] = [
                str(column) for column in original_column_snapshot
            ]
        if mapping_report is not None:
            metadata["column_mapping"] = mapping_report.get("column_mapping", {})
            metadata["mapping_decisions"] = mapping_report.get(
                "mapping_decisions", []
            )
            metadata["unmapped_source_columns"] = mapping_report.get(
                "unmapped_source_columns", []
            )
            metadata["normalized_column_snapshot"] = mapping_report.get(
                "normalized_column_snapshot", []
            )
            metadata["required_fields"] = mapping_report.get(
                "required_fields", []
            )

        return metadata
