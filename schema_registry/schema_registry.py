import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class SchemaRegistryError(Exception):
    """Raised when schema registry operations fail."""


class SchemaRegistry:
    """
    Loads and validates canonical schemas for supported ingestion sources.
    """

    SCHEMA_FILES: Dict[str, str] = {
        "sap": "sap_schema.json",
        "energy": "energy_schema.json",
        "rfid": "rfid_schema.json",
        "plc": "plc_schema.json",
        "generic": "generic_schema.json",
        # Internal source aliases
        "generic_tabular": "generic_schema.json",
        "operational_excel": "generic_schema.json",
        "report_excel": "sap_schema.json",
    }

    def __init__(self, registry_dir: Optional[Path] = None) -> None:
        self.registry_dir = Path(registry_dir or Path(__file__).resolve().parent)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_schema(self, source_type: str) -> Dict[str, Any]:
        normalized_source = self._resolve_source(source_type)
        if normalized_source in self._cache:
            return self._cache[normalized_source]

        schema_file = self.registry_dir / self.SCHEMA_FILES[normalized_source]
        if not schema_file.exists():
            raise SchemaRegistryError(
                f"Schema file not found for source '{source_type}': {schema_file}"
            )

        with open(schema_file, "r", encoding="utf-8") as handle:
            schema = json.load(handle)

        self._validate_schema_structure(schema, normalized_source)
        self._cache[normalized_source] = schema
        return schema

    def get_alias_lookup(self, source_type: str) -> Dict[str, str]:
        schema = self.load_schema(source_type)
        alias_lookup: Dict[str, str] = {}

        for field in schema["canonical_fields"]:
            canonical_name = field["canonical_name"]
            aliases = [canonical_name, *field.get("aliases", [])]
            for alias in aliases:
                normalized_alias = self.normalize_header(alias)
                if not normalized_alias:
                    continue
                existing = alias_lookup.get(normalized_alias)
                if existing and existing != canonical_name:
                    raise SchemaRegistryError(
                        f"Alias collision '{normalized_alias}' between "
                        f"'{existing}' and '{canonical_name}' in source "
                        f"'{source_type}'"
                    )
                alias_lookup[normalized_alias] = canonical_name

        return alias_lookup

    def get_required_fields(self, source_type: str) -> List[str]:
        schema = self.load_schema(source_type)
        required = [
            field["canonical_name"]
            for field in schema["canonical_fields"]
            if bool(field.get("required"))
        ]
        return required

    def validate_required_fields(
        self,
        source_type: str,
        raw_columns: Iterable[str],
    ) -> None:
        required_fields = set(self.get_required_fields(source_type))
        if not required_fields:
            return

        alias_lookup = self.get_alias_lookup(source_type)
        detected = set()
        for raw_column in raw_columns:
            normalized = self.normalize_header(raw_column)
            canonical = alias_lookup.get(normalized)
            if canonical:
                detected.add(canonical)

        missing = sorted(required_fields - detected)
        if missing:
            raise SchemaRegistryError(
                f"Missing required fields for source '{source_type}': {missing}"
            )

    def schema_version(self, source_type: str) -> str:
        schema = self.load_schema(source_type)
        return str(schema.get("schema_version", "unknown"))

    def detect_source_from_columns(
        self,
        raw_columns: Iterable[str],
        candidates: Optional[Iterable[str]] = None,
    ) -> Optional[str]:
        normalized_columns = {
            self.normalize_header(column)
            for column in raw_columns
            if self.normalize_header(column)
        }
        if not normalized_columns:
            return None

        source_candidates = list(candidates) if candidates else [
            "sap",
            "energy",
            "rfid",
            "plc",
            "generic",
        ]

        scored: List[Tuple[str, float]] = []
        for source in source_candidates:
            schema = self.load_schema(source)
            required = {
                field["canonical_name"]
                for field in schema["canonical_fields"]
                if bool(field.get("required"))
            }
            alias_lookup = self.get_alias_lookup(source)
            detected = {
                alias_lookup[column]
                for column in normalized_columns
                if column in alias_lookup
            }

            required_score = 0.0
            if required:
                required_hits = len(required.intersection(detected))
                required_score = required_hits / float(len(required))

            optional_fields = {
                field["canonical_name"]
                for field in schema["canonical_fields"]
                if not bool(field.get("required"))
            }
            optional_hits = len(optional_fields.intersection(detected))
            optional_score = (
                optional_hits / float(max(len(optional_fields), 1))
            )

            score = required_score * 0.8 + optional_score * 0.2
            scored.append((source, score))

        if not scored:
            return None

        scored.sort(key=lambda item: (-item[1], item[0]))
        top_source, top_score = scored[0]
        if top_score < 0.35:
            return None

        if len(scored) > 1 and abs(scored[0][1] - scored[1][1]) < 0.05:
            return None

        return top_source

    @staticmethod
    def normalize_header(value: Any) -> str:
        text = str(value).strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")

    def _resolve_source(self, source_type: str) -> str:
        normalized = self.normalize_header(source_type)
        if normalized not in self.SCHEMA_FILES:
            valid = sorted(
                {
                    key
                    for key in self.SCHEMA_FILES.keys()
                    if key not in {"generic_tabular", "report_excel", "operational_excel"}
                }
            )
            raise SchemaRegistryError(
                f"Unknown source type '{source_type}'. Valid sources: {valid}"
            )
        return normalized

    @staticmethod
    def _validate_schema_structure(schema: Dict[str, Any], source_type: str) -> None:
        if "canonical_fields" not in schema or not isinstance(
            schema["canonical_fields"], list
        ):
            raise SchemaRegistryError(
                f"Schema '{source_type}' missing 'canonical_fields' list"
            )

        required_keys = {
            "canonical_name",
            "aliases",
            "required",
            "data_type",
            "transform_rule",
        }
        seen: set[str] = set()
        for field in schema["canonical_fields"]:
            if not isinstance(field, dict):
                raise SchemaRegistryError(
                    f"Invalid field definition in schema '{source_type}': {field}"
                )

            missing_keys = required_keys.difference(field.keys())
            if missing_keys:
                raise SchemaRegistryError(
                    f"Schema '{source_type}' field missing keys {sorted(missing_keys)}"
                )

            canonical_name = str(field["canonical_name"]).strip()
            if not canonical_name:
                raise SchemaRegistryError(
                    f"Schema '{source_type}' contains empty canonical_name"
                )

            normalized_name = SchemaRegistry.normalize_header(canonical_name)
            if normalized_name in seen:
                raise SchemaRegistryError(
                    f"Duplicate canonical_name '{canonical_name}' in '{source_type}'"
                )
            seen.add(normalized_name)
