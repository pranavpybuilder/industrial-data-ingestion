"""
Generic Tabular Ingestor — Schema-Agnostic, Domain Auto-Detecting

Handles ANY CSV or XLSX file with unknown schema via:
1. Robust multi-encoding, multi-delimiter reading (CSVReader / ExcelReader)
2. Column normalization (lowercase, underscores, dedup)
3. Intelligent type casting (numeric detection, datetime detection)
4. Domain auto-detection (keyword scoring across column names + sample values)
5. Time column auto-resolution
6. Parquet persistence for downstream ML/rules/profiling

Tested against: Breakdown_data.csv (Plant 1152)
  - 57 rows, 46 columns (after dedup: notifictn_type, created_on, abc_indic,
    maintplant, coding, location, equipment, description, notification,
    description_2, system_status, user_status, breakdown_dur, order,
    malfunct_start, mal_start_t, malfunct_end, malfunction_end, breakdown,
    coding_code_txt, functional_loc, created_by, changed_by, changed_on,
    reported_by, long_text, why1, why_2, why_3, why_4, why_5,
    due_to_1, due_to_2, due_to_3, due_to_4, due_to_5,
    counters_measure, sustenance, horizontal_depl_pla, resposibility,
    root_cause, breakdown_attended_b, why_why_done_by, action_taken_to_solv,
    spare_part_replaced, kaizen_idea, kaizen_schedule)
  - Domain detected: maintenance (keywords: breakdown, malfunction, equipment,
    maintenance, why, repair, notification, coding)
"""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.csv_reader import CSVReader
from ingestion.readers.excel_reader import ExcelReader


# ─── Domain auto-detection signatures ────────────────────────────────────────

DOMAIN_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "maintenance": {
        "keywords": [
            "breakdown", "failure", "repair", "maintenance", "equipment",
            "notification", "malfunction", "downtime", "mttr", "mtbf",
            "work_order", "spare_part", "preventive", "corrective",
            "root_cause", "why", "coding", "malfunct", "breakdown_dur",
            "pm_overdue", "work_center", "functional_loc",
        ],
        "weight": 1.0,
    },
    "production": {
        "keywords": [
            "production", "output", "yield", "throughput", "cycle_time",
            "shift", "operator", "target", "actual", "oee", "efficiency",
            "batch", "lot", "quantity_produced", "rejection",
        ],
        "weight": 1.0,
    },
    "energy": {
        "keywords": [
            "kwh", "energy", "power", "consumption", "meter", "voltage",
            "current", "demand", "load", "tariff", "peak", "kva", "pf",
            "watt", "ampere",
        ],
        "weight": 1.0,
    },
    "quality": {
        "keywords": [
            "defect", "rejection", "rework", "inspection", "quality",
            "tolerance", "specification", "ncr", "ppk", "cpk",
            "scrap", "first_pass", "reject_rate",
        ],
        "weight": 1.0,
    },
    "safety": {
        "keywords": [
            "incident", "accident", "near_miss", "hazard", "safety",
            "injury", "lti", "ppe", "permit", "risk", "severity_safety",
        ],
        "weight": 1.0,
    },
    "inventory": {
        "keywords": [
            "stock", "inventory", "part", "material", "quantity", "bin",
            "warehouse", "reorder", "supplier", "purchase", "mrp",
        ],
        "weight": 1.0,
    },
    "plc": {
        "keywords": [
            "tag", "address", "signal", "plc", "opc", "register",
            "coil", "alarm", "setpoint", "process_value",
        ],
        "weight": 1.0,
    },
    "rfid": {
        "keywords": [
            "rfid", "tag_id", "reader", "scan", "antenna",
            "epc", "uid", "location_id",
        ],
        "weight": 1.0,
    },
}


def detect_domain(df: pd.DataFrame) -> str:
    """
    Score all column names + sample values against domain keywords.
    Returns the best-matching domain or 'generic' if no match.
    """
    # Build text corpus from column names
    text = " ".join(str(c).lower() for c in df.columns)

    # Also sample first 20 rows of string columns for keyword hits
    object_cols = df.select_dtypes(include="object").columns[:10]
    for col in object_cols:
        sample_vals = df[col].dropna().head(20).astype(str).tolist()
        text += " " + " ".join(v.lower() for v in sample_vals)

    scores: Dict[str, float] = {}
    for domain, config in DOMAIN_SIGNATURES.items():
        score = sum(1 for kw in config["keywords"] if kw in text)
        scores[domain] = score * config["weight"]

    best_domain = max(scores, key=lambda k: scores[k])
    return best_domain if scores[best_domain] > 0 else "generic"


# ─── Time column candidates ─────────────────────────────────────────────────

TIME_COLUMN_CANDIDATES = [
    "event_time", "created_on", "start_date", "date", "report_date",
    "timestamp", "malfunct_start", "malfunct_end", "malfunction_end",
    "mal_start_t", "changed_on", "created_at", "order_date",
    "event_date", "occurred_at",
]


def resolve_time_columns(df: pd.DataFrame) -> List[str]:
    """Find all columns that look like timestamps."""
    found: List[str] = []
    for candidate in TIME_COLUMN_CANDIDATES:
        if candidate in df.columns:
            found.append(candidate)

    # Also check column names containing 'date' or 'time'
    for col in df.columns:
        col_lower = str(col).lower()
        if col in found:
            continue
        if any(token in col_lower for token in ("date", "time", "timestamp")):
            found.append(col)

    return found


class GenericTabularIngestor(BaseIngestor):
    """
    Schema-agnostic ingestor for any CSV/XLSX file.

    Handles files with unknown structure by:
    1. Reading with robust encoding/delimiter fallback
    2. Normalizing column names
    3. Auto-detecting numeric columns (>85% parseable as numbers)
    4. Auto-detecting datetime columns
    5. Auto-detecting domain via keyword scoring
    6. Persisting as typed Parquet
    """

    def __init__(
        self,
        source_path: str,
        output_dir: str,
        run_id: Optional[str] = None,
        schema_type: str = "generic",
    ):
        # Use source_path filename as part of the source label
        file_stem = Path(source_path).stem.lower().replace(" ", "_")[:30]
        source_label = f"generic_{file_stem}"

        super().__init__(
            source_name=source_label,
            source_path=source_path,
            schema_path=None,
            output_dir=output_dir,
            run_id=run_id,
            # IMPORTANT: pass None for schema_type to skip schema registry lookup
            # The generic ingestor does NOT use the schema registry at all
            schema_type=None,
        )
        self._user_schema_type = schema_type
        self._detected_domain: str = "generic"

    def read(self) -> pd.DataFrame:
        """
        Read the raw file using the appropriate reader.

        For XLSX files with multiple sheets, reads ALL sheets and
        concatenates those with compatible schemas into one DataFrame.
        A ``_sheet_source`` column records which sheet each row came from.
        """
        path = Path(self.source_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return CSVReader.read(str(path), normalize_columns=True)

        if suffix in (".xlsx", ".xls"):
            return self._read_excel_all_sheets(path)

        if suffix == ".json":
            try:
                df = pd.read_json(str(path))
            except ValueError:
                df = pd.read_json(str(path), lines=True)
            return df

        raise ValueError(
            f"Unsupported file format '{suffix}'. "
            "Supported formats: .csv, .xlsx, .xls, .json"
        )

    def _read_excel_all_sheets(self, path: Path) -> pd.DataFrame:
        """
        Read an Excel workbook, iterating ALL sheets.

        Strategy:
        1. Read every sheet via ExcelReader.read_all_sheets()
        2. Score each sheet by row count and column count
        3. Pick the best sheet as the "primary" schema
        4. Concatenate all sheets whose columns overlap ≥60% with the primary
        5. Add a ``_sheet_source`` column so downstream knows the origin
        6. If only one usable sheet exists, return it as-is (fast path)
        """
        all_sheets = ExcelReader.read_all_sheets(
            file_path=str(path),
            header="auto",
            detect_dates=True,
            min_rows=1,
            min_cols=2,
        )

        if not all_sheets:
            # Fallback: try single-sheet read (may raise on truly empty files)
            return ExcelReader.read(
                file_path=str(path),
                sheet_name="auto",
                header="auto",
            )

        if len(all_sheets) == 1:
            name, df = next(iter(all_sheets.items()))
            df = df.copy()
            df["_sheet_source"] = name
            return df

        # Pick the primary (largest usable sheet)
        ranked = sorted(
            all_sheets.items(),
            key=lambda kv: len(kv[1]) * len(kv[1].columns),
            reverse=True,
        )
        primary_name, primary_df = ranked[0]
        primary_cols = set(primary_df.columns)

        # Collect compatible sheets (≥60% column overlap with primary)
        compatible: list[pd.DataFrame] = []
        for sheet_name, df in ranked:
            sheet_cols = set(df.columns)
            if not primary_cols:
                continue
            overlap = len(primary_cols & sheet_cols) / len(primary_cols)
            if overlap >= 0.60:
                tagged = df.copy()
                tagged["_sheet_source"] = sheet_name
                compatible.append(tagged)

        if not compatible:
            primary_df = primary_df.copy()
            primary_df["_sheet_source"] = primary_name
            return primary_df

        combined = pd.concat(compatible, ignore_index=True, sort=False)
        return combined

    def ingest(self) -> dict:
        """
        Full ingestion pipeline:
        1. Read raw data
        2. Validate not empty
        3. Normalize columns and types
        4. Detect domain
        5. Detect and parse time columns
        6. Persist to Parquet
        7. Return complete metadata
        """
        raw_df = self.read()
        self._validate_not_empty(raw_df)

        original_columns = list(raw_df.columns)

        # Normalize: clean column names, drop empty rows/cols, type coercion
        normalized_df = self._normalize(raw_df)
        self._validate_not_empty(normalized_df)

        # Auto-detect domain from normalized data
        self._detected_domain = detect_domain(normalized_df)

        # Auto-detect and parse datetime columns
        normalized_df = self._parse_datetime_columns(normalized_df)

        # Persist using base class (skips schema registry since schema_type=None)
        metadata = self.ingest_dataframe(
            data=normalized_df,
            original_column_snapshot=original_columns,
        )

        # Enrich metadata with domain and time info
        time_cols = resolve_time_columns(normalized_df)
        metadata["detected_domain"] = self._detected_domain
        metadata["detected_time_columns"] = time_cols
        metadata["detected_time_column"] = time_cols[0] if time_cols else None
        metadata["source_schema_type"] = self._detected_domain
        metadata["normalized_column_snapshot"] = list(normalized_df.columns)

        return metadata

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names and coerce numeric columns.

        Column name normalization:
        - Strip whitespace
        - Lowercase
        - Replace spaces/slashes with underscores
        - Remove non-alphanumeric characters (except underscores)
        - Collapse multiple underscores
        - Deduplicate names (append _2, _3, etc.)

        Type coercion:
        - Columns where ≥85% of values parse as numeric → float64
        """
        normalized = df.copy()

        # Normalize column names
        raw_cols = normalized.columns.astype(str).str.strip()
        clean_cols = (
            raw_cols
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
            .str.replace("/", "_")
            .str.replace(r"[^a-z0-9_]+", "", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )

        # Deduplicate column names
        seen: dict[str, int] = {}
        deduped: list[str] = []
        for name in clean_cols:
            if not name:
                name = "unnamed"
            if name in seen:
                seen[name] += 1
                deduped.append(f"{name}_{seen[name]}")
            else:
                seen[name] = 1
                deduped.append(name)

        normalized.columns = pd.Index(deduped)

        # Drop fully-empty rows and columns
        normalized = normalized.dropna(how="all").dropna(axis=1, how="all")
        normalized = normalized.reset_index(drop=True)

        # Auto-detect numeric columns
        for column in normalized.columns:
            if normalized[column].dtype == "object":
                numeric = pd.to_numeric(normalized[column], errors="coerce")
                non_null_original = normalized[column].notna().sum()
                if non_null_original > 0:
                    parse_rate = numeric.notna().sum() / non_null_original
                    if parse_rate >= 0.85:
                        normalized[column] = numeric

        return normalized

    def _parse_datetime_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Auto-detect and parse datetime columns.
        Only parses columns whose names contain date/time tokens AND
        where ≥40% of non-null values parse as valid dates.
        """
        result = df.copy()
        datetime_tokens = ("date", "time", "timestamp", "start", "end", "created", "changed")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format")

            for col in result.columns:
                col_lower = str(col).lower()
                # Skip columns already numeric
                if pd.api.types.is_numeric_dtype(result[col]):
                    continue
                # Only try columns whose names suggest datetime
                if not any(token in col_lower for token in datetime_tokens):
                    continue

                series = result[col]
                if series.dtype == "object" or series.dtype.name == "string":
                    non_null = series.dropna()
                    if len(non_null) < 3:
                        continue

                    parsed = pd.to_datetime(non_null.astype(str).str.strip(), errors="coerce")
                    valid_rate = parsed.notna().sum() / len(non_null)

                    if valid_rate >= 0.40:
                        result[col] = pd.to_datetime(
                            series.astype(str).str.strip(),
                            errors="coerce",
                        )

        return result
