import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from utils.paths import MODEL_DIR


class ModelRegistry:
    """
    Simple local model artifact registry (offline, run-scoped).
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir or MODEL_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        run_id: str,
        model_name: str,
        model: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        model_path = run_dir / f"{model_name}.joblib"
        metadata_path = run_dir / f"{model_name}.metadata.json"

        joblib.dump(model, model_path)
        if metadata is None:
            metadata = {}

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {
            "model_path": str(model_path),
            "metadata_path": str(metadata_path),
        }
