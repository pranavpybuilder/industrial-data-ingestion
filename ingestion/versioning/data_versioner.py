import json
from pathlib import Path
from datetime import datetime
import pandas as pd


class DataVersioner:
    """
    Handles versioned persistence of ingested datasets.

    Each ingestion run is stored in an immutable, versioned directory
    along with metadata required for auditing and ML reproducibility.
    """

    def __init__(self, base_output_dir: Path):
        """
        Parameters
        ----------
        base_output_dir : Path
            Base directory where versioned data will be stored
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        data: pd.DataFrame,
        filename: str,
        run_id: str,
    ) -> Path:
        """
        Persist a versioned snapshot of the dataset.

        Parameters
        ----------
        data : pd.DataFrame
            Validated DataFrame to persist
        filename : str
            Base filename (e.g., 'rfid.parquet')
        run_id : str
            Unique ingestion run ID

        Returns
        -------
        Path
            Path to the saved dataset file
        """

        run_dir = self._create_run_directory(run_id)

        dataset_path = run_dir / filename
        metadata_path = run_dir / "metadata.json"

        # Persist dataset (Parquet is ML-efficient and schema-safe)
        data.to_parquet(dataset_path, index=False)

        # Persist metadata
        metadata = self._build_metadata(data, run_id, dataset_path)
        self._write_metadata(metadata_path, metadata)

        return dataset_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_run_directory(self, run_id: str) -> Path:
        """
        Create a directory for a specific ingestion run.
        """
        run_dir = self.base_output_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir

    def _build_metadata(
        self,
        data: pd.DataFrame,
        run_id: str,
        dataset_path: Path,
    ) -> dict:
        """
        Build metadata describing the ingestion snapshot.
        """
        return {
            "run_id": run_id,
            "created_at": datetime.utcnow().isoformat(),
            "rows": int(len(data)),
            "columns": list(data.columns),
            "dataset_path": str(dataset_path),
            "format": "parquet",
        }

    def _write_metadata(self, path: Path, metadata: dict) -> None:
        """
        Write metadata JSON to disk.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)