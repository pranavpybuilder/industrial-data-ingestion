"""
File upload handler for ingestion.

Responsibilities:
- Resolve source type (explicit or auto-detected from headers)
- Auto-detect domain for unknown file schemas
- Instantiate the correct source ingestor
- Execute ingestion and return stable metadata contract
- Graceful fallback: any file that doesn't match known schemas goes through
  GenericTabularIngestor with domain auto-detection

Production behavior:
- NEVER crashes — always returns {success: bool, error?: str, ...metadata}
- Source type resolution order:
  1. Explicit source_type param → use directly
  2. Schema registry header match → known source (SAP, PLC, RFID, etc.)
  3. Generic tabular → auto-detects domain (maintenance, production, energy, etc.)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ingestion.sources.generic_tabular_ingestor import GenericTabularIngestor
from ingestion.sources.operational_excel_ingestor import OperationalExcelIngestor
from ingestion.sources.plc_ingestor import PLCIngestor
from ingestion.sources.report_excel_ingestor import ReportExcelIngestor
from ingestion.sources.rfid_ingestor import RFIDIngestor
from ingestion.sources.sap_ingestor import SAPIngestor
from ingestion.readers.excel_reader import ExcelReader
from ingestion.readers.csv_reader import CSVReader
from schema_registry.schema_registry import SchemaRegistry
from utils.logger import get_logger
from utils.paths import RAW_DATA_DIR

logger = get_logger(__name__)
schema_registry = SchemaRegistry()

_CONTRACTS_DIR = Path(__file__).parent / "contracts"

# ─── Source Registry ─────────────────────────────────────────────────────────
# Maps source type names to their ingestor class, schema path, and output dir.
# GenericTabularIngestor is the catch-all for any unknown schema type.

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sap": {
        "ingestor": SAPIngestor,
        "schema": str(_CONTRACTS_DIR / "sap_iw29_schema.json"),
        "output_dir": str(RAW_DATA_DIR / "sap"),
    },
    "plc": {
        "ingestor": PLCIngestor,
        "schema": str(_CONTRACTS_DIR / "plc_schema.json"),
        "output_dir": str(RAW_DATA_DIR / "plc"),
    },
    "rfid": {
        "ingestor": RFIDIngestor,
        "schema": str(_CONTRACTS_DIR / "rfid_schema.json"),
        "output_dir": str(RAW_DATA_DIR / "rfid"),
    },
    "report_excel": {
        "ingestor": ReportExcelIngestor,
        "schema": str(_CONTRACTS_DIR / "report_excel_schema.json"),
        "output_dir": str(RAW_DATA_DIR / "report_excel"),
    },
    "energy": {
        "ingestor": GenericTabularIngestor,
        "schema": None,
        "output_dir": str(RAW_DATA_DIR / "energy"),
        "schema_type": "energy",
    },
    "operational_excel": {
        "ingestor": OperationalExcelIngestor,
        "schema": None,
        "output_dir": str(RAW_DATA_DIR / "operational_excel"),
        "schema_type": "generic",
    },
    "generic_tabular": {
        "ingestor": GenericTabularIngestor,
        "schema": None,
        "output_dir": str(RAW_DATA_DIR / "generic_tabular"),
        "schema_type": "generic",
    },
}

# ─── Extension → candidate source types ──────────────────────────────────────
_EXTENSION_HINTS: Dict[str, List[str]] = {
    ".csv": ["sap", "energy", "plc", "rfid", "generic_tabular"],
    ".json": ["plc", "rfid", "generic_tabular"],
    ".xlsx": ["report_excel", "energy", "sap", "generic_tabular", "operational_excel"],
    ".xls": ["report_excel", "energy", "sap", "generic_tabular", "operational_excel"],
    ".log": ["plc"],
    ".txt": ["plc"],
    ".tsv": ["generic_tabular"],
    ".parquet": ["generic_tabular"],
}

# Maps a source type to its schema type in the schema registry
SOURCE_TO_SCHEMA_TYPE: Dict[str, str] = {
    "sap": "sap",
    "report_excel": "sap",
    "plc": "plc",
    "rfid": "rfid",
    "energy": "energy",
    "generic_tabular": "generic",
    "operational_excel": "generic",
}


# ─── Public API ──────────────────────────────────────────────────────────────


def detect_source_type(file_path: str) -> Optional[str]:
    """
    Auto-detect the source type of a file by inspecting its headers.

    Strategy:
    1. Look at file extension → get candidate source types
    2. Preview headers → try schema registry matching
    3. Fallback to generic_tabular (which then does domain auto-detection)

    Returns
    -------
    str or None
        Detected source type, or None if detection fails entirely.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    candidates = _EXTENSION_HINTS.get(suffix, [])

    if not candidates:
        # Unknown extension — try generic if it's a text-like file
        return "generic_tabular"

    if len(candidates) == 1:
        return candidates[0]

    # Try to read headers and match against schema registry
    headers = _preview_headers(path)
    if not headers:
        return "generic_tabular" if "generic_tabular" in candidates else candidates[0]

    # Get unique schema type candidates
    candidate_schemas = sorted({
        SOURCE_TO_SCHEMA_TYPE.get(candidate, "generic")
        for candidate in candidates
    })

    try:
        detected_schema = schema_registry.detect_source_from_columns(
            raw_columns=headers,
            candidates=candidate_schemas,
        )
    except Exception:
        detected_schema = None

    if detected_schema is None:
        return "generic_tabular" if "generic_tabular" in candidates else candidates[0]

    return _resolve_source_from_schema(
        detected_schema=detected_schema,
        candidates=candidates,
        file_suffix=suffix,
    )


def handle_file_upload(
    file_path: str,
    source_type: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle a file upload: detect type, instantiate ingestor, run pipeline.

    Always returns a dict with at least:
        {"success": bool, "error"?: str, ...metadata}

    Never raises — all exceptions are caught and returned as error messages.

    Parameters
    ----------
    file_path : str
        Absolute path to the file to ingest.
    source_type : str, optional
        Explicit source type. If None, auto-detected from headers.
    run_id : str, optional
        Run ID to use. If None, auto-generated.

    Returns
    -------
    dict
        Ingestion metadata with success flag.
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {file_path}"
        logger.error(msg)
        return {"success": False, "error": msg}

    # Resolve source type
    if source_type is None:
        source_type = detect_source_type(file_path) or "generic_tabular"
        logger.info("Auto-detected source type: %s for file: %s", source_type, path.name)

    source_type = source_type.lower().strip()

    # If the source type isn't in the registry, fall back to generic
    if source_type not in SOURCE_REGISTRY:
        logger.warning(
            "Unknown source type '%s' — falling back to generic_tabular. "
            "Valid types: %s",
            source_type,
            sorted(SOURCE_REGISTRY.keys()),
        )
        source_type = "generic_tabular"

    config = SOURCE_REGISTRY[source_type]
    ingestor_cls = config["ingestor"]

    try:
        # Instantiate the correct ingestor based on source type
        if ingestor_cls is GenericTabularIngestor:
            ingestor = ingestor_cls(
                source_path=file_path,
                output_dir=config["output_dir"],
                run_id=run_id,
                schema_type=config.get("schema_type", "generic"),
            )
        elif source_type == "operational_excel":
            ingestor = ingestor_cls(
                source_path=file_path,
                output_dir=config["output_dir"],
                run_id=run_id,
            )
        else:
            ingestor = ingestor_cls(
                source_path=file_path,
                schema_path=config["schema"],
                output_dir=config["output_dir"],
                run_id=run_id,
            )

        logger.info("Starting ingestion: %s as '%s'", path.name, source_type)
        metadata = ingestor.ingest()
        logger.info(
            "Ingestion complete: rows=%s columns=%s run_id=%s",
            metadata.get("rows", 0),
            len(metadata.get("columns", [])),
            metadata.get("run_id"),
        )

        # Ensure source type is always set correctly in metadata
        internal_source = metadata.get("source", source_type)
        metadata["source"] = source_type
        metadata["ingestor_source"] = internal_source

        return {
            "success": True,
            "error": None,
            **metadata,
        }

    except Exception as exc:
        msg = f"Ingestion failed for '{path.name}': {exc}"
        logger.error(msg, exc_info=True)
        return {"success": False, "error": msg}


# ─── Internal Helpers ────────────────────────────────────────────────────────


def _preview_headers(path: Path) -> List[str]:
    """
    Read only the headers from a file for source type detection.
    Uses robust encoding fallback for CSV files.
    """
    try:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            # Use CSVReader's robust encoding for header preview
            df = CSVReader.read(str(path), normalize_columns=True)
            return list(df.columns)
        if suffix == ".json":
            try:
                df = pd.read_json(path, nrows=20)
            except Exception:
                try:
                    df = pd.read_json(path, lines=True, nrows=20)
                except Exception:
                    return []
            return [str(c) for c in df.columns]
        if suffix in (".xlsx", ".xls"):
            df = ExcelReader.read(
                file_path=str(path),
                sheet_name="auto",
                header="auto",
                detect_dates=False,
            )
            return [str(c) for c in df.columns]
    except Exception:
        return []
    return []


def _resolve_source_from_schema(
    detected_schema: str,
    candidates: List[str],
    file_suffix: str,
) -> Optional[str]:
    """
    Given a detected schema type and a list of candidate source types,
    resolve the best matching source type.
    """
    for candidate in candidates:
        if SOURCE_TO_SCHEMA_TYPE.get(candidate) != detected_schema:
            continue

        if detected_schema == "sap":
            if file_suffix in (".xlsx", ".xls") and candidate == "report_excel":
                return candidate
            if file_suffix == ".csv" and candidate == "sap":
                return candidate
        else:
            return candidate

    # Fallback resolution
    if detected_schema == "generic":
        if "operational_excel" in candidates and file_suffix in (".xlsx", ".xls"):
            return "operational_excel"
        if "generic_tabular" in candidates:
            return "generic_tabular"

    if detected_schema == "energy" and "energy" in candidates:
        return "energy"

    return candidates[0] if candidates else None
