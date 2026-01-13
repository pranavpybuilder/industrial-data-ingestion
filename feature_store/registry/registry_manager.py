from pathlib import Path
from typing import Dict
import yaml


class FeatureRegistryManager:
    """
    Manages the Feature Store registry which tracks feature definitions,
    versions, ownership, and last update metadata.
    """

    def __init__(self, registry_path: str) -> None:
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.registry_path.exists():
            self._initialize_registry()

    def _initialize_registry(self) -> None:
        """
        Initialize an empty feature registry file.
        """
        initial_registry = {
            "version": "1.0",
            "features": {}
        }

        with open(self.registry_path, "w") as f:
            yaml.safe_dump(initial_registry, f)

    def _load_registry(self) -> Dict:
        with open(self.registry_path, "r") as f:
            return yaml.safe_load(f)

    def _save_registry(self, registry: Dict) -> None:
        with open(self.registry_path, "w") as f:
            yaml.safe_dump(registry, f)

    def register_feature(
        self,
        feature_name: str,
        entity: str,
        source: str,
        version: str,
        owner: str,
        description: str
    ) -> None:
        """
        Register or update a feature in the registry.
        """
        registry = self._load_registry()

        registry["features"][feature_name] = {
            "entity": entity,
            "source": source,
            "version": version,
            "owner": owner,
            "description": description,
        }

        self._save_registry(registry)

    def get_feature(self, feature_name: str) -> Dict | None:
        """
        Retrieve a feature entry from the registry.
        """
        registry = self._load_registry()
        return registry["features"].get(feature_name)

    def list_features(self) -> Dict:
        """
        List all registered features.
        """
        registry = self._load_registry()
        return registry.get("features", {})