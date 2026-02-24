from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from schema_registry.schema_registry import SchemaRegistry


class ColumnMappingError(Exception):
    """Raised when canonical column mapping fails."""


class ColumnMapper:
    """
    Deterministic canonical column mapper.

    Steps:
    1. Normalize headers
    2. Exact alias matching
    3. Fuzzy alias matching (deterministic tie-breaking)
    4. Canonical renaming + transform enforcement
    5. Required field validation
    """

    ALLOW_MISSING_REQUIRED_RULES = {"to_int_default_one"}

    def __init__(self, fuzzy_threshold: float = 0.84) -> None:
        self.fuzzy_threshold = fuzzy_threshold

    def map_dataframe(
        self,
        df: pd.DataFrame,
        schema: Dict[str, Any],
        source_type: str,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        if df is None or df.empty:
            raise ColumnMappingError("Cannot map an empty dataframe")

        original_columns = [str(column) for column in df.columns]
        normalized_pairs = [
            (column, SchemaRegistry.normalize_header(column))
            for column in original_columns
        ]
        self._ensure_unique_normalized_headers(normalized_pairs)

        normalized_to_original = {
            normalized: original
            for original, normalized in normalized_pairs
        }

        normalized_df = df.copy()
        normalized_df.columns = [normalized for _, normalized in normalized_pairs]
        source_columns = list(normalized_df.columns)

        canonical_fields = schema.get("canonical_fields", [])
        mapped: Dict[str, str] = {}
        mapped_decisions: List[Dict[str, Any]] = []
        used_source_columns: Set[str] = set()

        # Phase 1: exact alias mapping
        for field in canonical_fields:
            canonical_name = field["canonical_name"]
            aliases = self._field_aliases(field)
            for alias in aliases:
                if alias in source_columns and alias not in used_source_columns:
                    mapped[canonical_name] = alias
                    used_source_columns.add(alias)
                    mapped_decisions.append(
                        {
                            "canonical_name": canonical_name,
                            "source_column": normalized_to_original.get(alias, alias),
                            "match_method": "exact",
                            "match_alias": alias,
                            "score": 1.0,
                        }
                    )
                    break

        # Phase 2: fuzzy matching for unmapped canonical fields
        for field in canonical_fields:
            canonical_name = field["canonical_name"]
            if canonical_name in mapped:
                continue

            candidate_columns = [
                column
                for column in source_columns
                if column not in used_source_columns
            ]
            if not candidate_columns:
                continue

            best_column, best_alias, best_score = self._best_fuzzy_match(
                candidate_columns=candidate_columns,
                aliases=self._field_aliases(field),
            )
            if (
                best_column is None
                or best_alias is None
                or best_score < self.fuzzy_threshold
            ):
                continue

            mapped[canonical_name] = best_column
            used_source_columns.add(best_column)
            mapped_decisions.append(
                {
                    "canonical_name": canonical_name,
                    "source_column": normalized_to_original.get(best_column, best_column),
                    "match_method": "fuzzy",
                    "match_alias": best_alias,
                    "score": round(best_score, 4),
                }
            )

        required_fields = [
            field["canonical_name"]
            for field in canonical_fields
            if bool(field.get("required"))
        ]
        missing_required = [
            field["canonical_name"]
            for field in canonical_fields
            if bool(field.get("required"))
            and field["canonical_name"] not in mapped
            and str(field.get("transform_rule", "")).strip().lower()
            not in self.ALLOW_MISSING_REQUIRED_RULES
        ]
        if missing_required:
            raise ColumnMappingError(
                f"Schema mapping failed for source '{source_type}'. "
                f"Missing required canonical fields: {sorted(missing_required)}. "
                f"Available columns: {original_columns}"
            )

        rename_map = {source: canonical for canonical, source in mapped.items()}
        canonical_df = normalized_df.rename(columns=rename_map)

        # Ensure all canonical fields exist for deterministic downstream contracts.
        for field in canonical_fields:
            canonical_name = field["canonical_name"]
            if canonical_name in canonical_df.columns:
                continue

            transform_rule = str(field.get("transform_rule", "")).strip().lower()
            if transform_rule == "to_int_default_one":
                canonical_df[canonical_name] = 1
                mapped_decisions.append(
                    {
                        "canonical_name": canonical_name,
                        "source_column": None,
                        "match_method": "default",
                        "match_alias": None,
                        "score": 0.0,
                    }
                )
            else:
                canonical_df[canonical_name] = pd.NA

        # Apply transforms and enforce expected dtypes.
        for field in canonical_fields:
            canonical_name = field["canonical_name"]
            transformed = self._apply_transform(
                series=canonical_df[canonical_name],
                transform_rule=str(field.get("transform_rule", "identity")),
                data_type=str(field.get("data_type", "string")),
                required=bool(field.get("required")),
                column_name=canonical_name,
            )
            canonical_df[canonical_name] = transformed

        # Required fields must contain at least one non-null value.
        for field in canonical_fields:
            canonical_name = field["canonical_name"]
            if not bool(field.get("required")):
                continue
            if canonical_df[canonical_name].notna().sum() == 0:
                raise ColumnMappingError(
                    f"Required field '{canonical_name}' is fully null "
                    f"after transformation for source '{source_type}'"
                )

        canonical_order = [field["canonical_name"] for field in canonical_fields]
        extra_columns = [
            column
            for column in canonical_df.columns
            if column not in canonical_order
        ]
        canonical_df = canonical_df[canonical_order + sorted(extra_columns)]

        unmapped_source_columns = [
            normalized_to_original[column]
            for column in source_columns
            if column not in set(mapped.values())
        ]

        mapping_report = {
            "source_type": source_type,
            "schema_version": schema.get("schema_version", "unknown"),
            "required_fields": required_fields,
            "column_mapping": {
                canonical: normalized_to_original[source]
                for canonical, source in mapped.items()
            },
            "mapping_decisions": mapped_decisions,
            "original_column_snapshot": original_columns,
            "normalized_column_snapshot": source_columns,
            "unmapped_source_columns": unmapped_source_columns,
        }

        return canonical_df, mapping_report

    def _best_fuzzy_match(
        self,
        candidate_columns: List[str],
        aliases: List[str],
    ) -> Tuple[Optional[str], Optional[str], float]:
        best_column: Optional[str] = None
        best_alias: Optional[str] = None
        best_score = -1.0

        for column in sorted(candidate_columns):
            for alias in sorted(aliases):
                score = self._similarity(column, alias)
                if score > best_score:
                    best_score = score
                    best_column = column
                    best_alias = alias
                    continue

                if score == best_score:
                    candidate_tuple = (column, alias)
                    best_tuple = (best_column or "", best_alias or "")
                    if candidate_tuple < best_tuple:
                        best_column = column
                        best_alias = alias

        return best_column, best_alias, best_score

    @staticmethod
    def _field_aliases(field: Dict[str, Any]) -> List[str]:
        aliases = [field["canonical_name"], *field.get("aliases", [])]
        normalized = [
            SchemaRegistry.normalize_header(alias)
            for alias in aliases
            if SchemaRegistry.normalize_header(alias)
        ]
        deduplicated = list(dict.fromkeys(normalized))
        return deduplicated

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        ratio = SequenceMatcher(None, left, right).ratio()

        left_tokens = set(filter(None, left.split("_")))
        right_tokens = set(filter(None, right.split("_")))
        union = left_tokens.union(right_tokens)
        token_overlap = (
            len(left_tokens.intersection(right_tokens)) / float(len(union))
            if union
            else 0.0
        )

        return ratio * 0.75 + token_overlap * 0.25

    @staticmethod
    def _ensure_unique_normalized_headers(
        normalized_pairs: List[Tuple[str, str]],
    ) -> None:
        by_normalized: Dict[str, List[str]] = {}
        for original, normalized in normalized_pairs:
            by_normalized.setdefault(normalized, []).append(original)

        collisions = {
            normalized: originals
            for normalized, originals in by_normalized.items()
            if len(originals) > 1
        }
        if collisions:
            raise ColumnMappingError(
                "Header normalization produced collisions: "
                f"{collisions}. Rename source columns to disambiguate."
            )

    def _apply_transform(
        self,
        series: pd.Series,
        transform_rule: str,
        data_type: str,
        required: bool,
        column_name: str,
    ) -> pd.Series:
        rule = transform_rule.strip().lower()
        dtype = data_type.strip().lower()
        transformed = series.copy()

        if rule in {"identity", ""}:
            pass
        elif rule == "to_string":
            transformed = transformed.astype("string").str.strip()
        elif rule == "lower_text":
            transformed = transformed.astype("string").str.strip().str.lower()
        elif rule == "upper_text":
            transformed = transformed.astype("string").str.strip().str.upper()
        elif rule == "to_float":
            transformed = self._to_numeric(
                transformed,
                required=required,
                column_name=column_name,
                allow_fraction=True,
            )
        elif rule == "to_int":
            transformed = self._to_numeric(
                transformed,
                required=required,
                column_name=column_name,
                allow_fraction=False,
            ).round().astype("Int64")
        elif rule == "to_int_default_one":
            numeric = pd.to_numeric(transformed, errors="coerce")
            if numeric.notna().sum() == 0:
                numeric = pd.Series(
                    [1] * len(transformed),
                    index=transformed.index,
                    dtype="float64",
                )
            else:
                numeric = numeric.fillna(1.0)
            transformed = numeric.round().astype("Int64")
        elif rule == "to_datetime_utc":
            raw_non_null = transformed.notna().sum()
            parsed = pd.to_datetime(transformed, errors="coerce", utc=True)
            invalid = int(raw_non_null - parsed.notna().sum())
            if required and invalid > 0:
                raise ColumnMappingError(
                    f"Failed datetime parse for required column '{column_name}'. "
                    f"Invalid values: {invalid}"
                )
            transformed = parsed
        elif rule == "to_bool":
            transformed = self._to_bool(transformed, required, column_name)
        else:
            raise ColumnMappingError(
                f"Unsupported transform rule '{transform_rule}' for "
                f"column '{column_name}'"
            )

        transformed = self._enforce_dtype(
            transformed,
            dtype=dtype,
            required=required,
            column_name=column_name,
        )
        return transformed

    def _to_numeric(
        self,
        series: pd.Series,
        required: bool,
        column_name: str,
        allow_fraction: bool,
    ) -> pd.Series:
        raw_non_null = series.notna().sum()
        numeric = pd.to_numeric(series, errors="coerce")
        invalid = int(raw_non_null - numeric.notna().sum())
        if required and invalid > 0:
            raise ColumnMappingError(
                f"Failed numeric parse for required column '{column_name}'. "
                f"Invalid values: {invalid}"
            )

        if not allow_fraction:
            numeric = numeric.round()

        return numeric

    @staticmethod
    def _to_bool(
        series: pd.Series,
        required: bool,
        column_name: str,
    ) -> pd.Series:
        mapped_values = {
            "true": True,
            "t": True,
            "1": True,
            "yes": True,
            "y": True,
            "false": False,
            "f": False,
            "0": False,
            "no": False,
            "n": False,
        }

        def _map_value(value: Any) -> Any:
            if pd.isna(value):
                return pd.NA
            if isinstance(value, bool):
                return value
            key = str(value).strip().lower()
            if key in mapped_values:
                return mapped_values[key]
            return pd.NA

        transformed = series.map(_map_value).astype("boolean")
        if required and transformed.notna().sum() == 0:
            raise ColumnMappingError(
                f"Failed boolean coercion for required column '{column_name}'"
            )
        return transformed

    def _enforce_dtype(
        self,
        series: pd.Series,
        dtype: str,
        required: bool,
        column_name: str,
    ) -> pd.Series:
        if dtype == "string":
            return series.astype("string")
        if dtype == "float":
            numeric = pd.to_numeric(series, errors="coerce")
            if required and numeric.notna().sum() == 0:
                raise ColumnMappingError(
                    f"Required float column '{column_name}' has no valid values"
                )
            return numeric.astype(float)
        if dtype == "int":
            numeric = pd.to_numeric(series, errors="coerce").round()
            if required and numeric.notna().sum() == 0:
                raise ColumnMappingError(
                    f"Required int column '{column_name}' has no valid values"
                )
            return numeric.astype("Int64")
        if dtype == "bool":
            return series.astype("boolean")
        if dtype == "datetime":
            parsed = pd.to_datetime(series, errors="coerce", utc=True)
            if required and parsed.notna().sum() == 0:
                raise ColumnMappingError(
                    f"Required datetime column '{column_name}' has no valid values"
                )
            return parsed

        raise ColumnMappingError(
            f"Unsupported data_type '{dtype}' for column '{column_name}'"
        )
