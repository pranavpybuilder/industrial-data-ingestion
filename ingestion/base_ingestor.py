from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import pandas as pd

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
        schema_path: str,
        output_dir: str,
    ):
        self.source_name = source_name
        self.source_path = Path(source_path)
        self.schema_path = Path(schema_path)
        self.output_dir = Path(output_dir)

        self.run_id = generate_run_id()
        self.ingestion_time = datetime.utcnow()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.versioner = DataVersioner(self.output_dir)

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

        # 1. Read
        data = self.read()
        self._validate_not_empty(data)

        # 2. Validate
        self._validate_schema(data)
        self._validate_types(data)
        self._validate_time(data)

        # 3. Version + Persist
        versioned_path = self._persist(data)

        # 4. Metadata
        return self._build_metadata(versioned_path, data)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_not_empty(self, data: pd.DataFrame):
        if data is None or data.empty:
            raise ValueError(
                f"[{self.source_name}] Ingestion failed: dataset is empty"
            )

    def _validate_schema(self, data: pd.DataFrame):
        SchemaValidator.validate(data, self.schema_path)

    def _validate_types(self, data: pd.DataFrame):
        TypeValidator.validate(data, self.schema_path)

    def _validate_time(self, data: pd.DataFrame):
        TimeValidator.validate(data, self.schema_path)

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

    def _build_metadata(self, path: Path, data: pd.DataFrame) -> dict:
        """
        Metadata returned to orchestration layer.
        """
        return {
            "source": self.source_name,
            "run_id": self.run_id,
            "rows": len(data),
            "columns": list(data.columns),
            "output_path": str(path),
            "ingested_at": self.ingestion_time.isoformat(),
        }
