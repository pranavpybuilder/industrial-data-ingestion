# ingestion/upload_handler.py

"""
File Upload Handler for the Ingestion Layer.

Responsibilities:
- Accept a file path and source type
- Auto-detect source type when not specified
- Instantiate the correct ingestor
- Execute ingestion pipeline
- Return structured metadata for downstream layers
"""

from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from ingestion.sources.sap_ingestor import SAPIngestor
from ingestion.sources.plc_ingestor import PLCIngestor
from ingestion.sources.rfid_ingestor import RFIDIngestor
from ingestion.sources.report_excel_ingestor import ReportExcelIngestor
from ingestion.sources.operational_excel_ingestor import OperationalExcelIngestor
from utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# Source type → (Ingestor class, schema path)
# ──────────────────────────────────────────────
_CONTRACTS_DIR = Path(__file__).parent / "contracts"

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sap": {
        "ingestor": SAPIngestor,
        "schema": str(_CONTRACTS_DIR / "sap_iw29_schema.json"),
        "output_dir": "data/raw/sap",
    },
    "plc": {
        "ingestor": PLCIngestor,
        "schema": str(_CONTRACTS_DIR / "plc_schema.json"),
        "output_dir": "data/raw/plc",
    },
    "rfid": {
        "ingestor": RFIDIngestor,
        "schema": str(_CONTRACTS_DIR / "rfid_schema.json"),
        "output_dir": "data/raw/rfid",
    },
    "report_excel": {
        "ingestor": ReportExcelIngestor,
        "schema": str(_CONTRACTS_DIR / "report_excel_schema.json"),
        "output_dir": "data/raw/reports",
    },
    "operational_excel": {
        "ingestor": OperationalExcelIngestor,
        "schema": None,  # schema-less by design
        "output_dir": "data/raw/operational_excels",
    },
}

# ──────────────────────────────────────────────
# File extension → candidate source types
# ──────────────────────────────────────────────
_EXTENSION_HINTS: Dict[str, list] = {
    ".csv": ["plc", "sap", "rfid"],
    ".json": ["plc", "rfid"],
    ".xlsx": ["report_excel", "sap", "operational_excel"],
    ".xls": ["report_excel", "sap", "operational_excel"],
    ".log": ["plc"],
    ".txt": ["plc"],
}


def detect_source_type(file_path: str) -> Optional[str]:
    """
    Attempt to auto-detect source type from file extension and content.

    Returns the best-guess source type string, or None if ambiguous.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    candidates = _EXTENSION_HINTS.get(suffix, [])

    if len(candidates) == 1:
        return candidates[0]

    # If CSV or JSON, peek at columns to disambiguate
    if suffix == ".csv":
        return _detect_from_csv(path)
    elif suffix == ".json":
        return _detect_from_json(path)
    elif suffix in (".xlsx", ".xls"):
        return _detect_from_excel(path)

    return None


def _detect_from_csv(path: Path) -> Optional[str]:
    """Peek at CSV headers to detect source type."""
    try:
        df = pd.read_csv(path, nrows=0)
        cols = {c.strip().lower().replace(" ", "_") for c in df.columns}
    except Exception:
        return None

    if {"machine_id", "event_time", "parameter_name"}.issubset(cols):
        return "plc"
    if {"order_number", "equipment_id", "start_date"}.issubset(cols):
        return "sap"
    if {"tag_id", "event_time", "reader_id"}.issubset(cols):
        return "rfid"

    return None


def _detect_from_json(path: Path) -> Optional[str]:
    """Peek at JSON keys to detect source type."""
    try:
        df = pd.read_json(path, nrows=5)
        cols = {c.strip().lower().replace(" ", "_") for c in df.columns}
    except Exception:
        return None

    if {"machine_id", "event_time", "parameter_name"}.issubset(cols):
        return "plc"
    if {"tag_id", "event_time", "reader_id"}.issubset(cols):
        return "rfid"

    return None


def _detect_from_excel(path: Path) -> Optional[str]:
    """Peek at Excel headers to detect source type."""
    try:
        df = pd.read_excel(str(path), nrows=5, header=0)
        cols = {
            str(c).strip().lower().replace(" ", "_")
            for c in df.columns
        }
    except Exception:
        return None

    # Report Excel signature
    if {"date", "equipment_number", "machine_name", "downtime"}.issubset(cols):
        return "report_excel"
    # SAP signature
    if {"order_number", "equipment_id", "start_date"}.issubset(cols):
        return "sap"

    # Fallback: treat as operational excel (schema-less)
    return "operational_excel"


# ──────────────────────────────────────────────
# Main upload handler
# ──────────────────────────────────────────────

def handle_file_upload(
    file_path: str,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle a single file upload through the ingestion pipeline.

    Parameters
    ----------
    file_path : str
        Absolute path to the uploaded file
    source_type : str, optional
        One of: sap, plc, rfid, report_excel, operational_excel.
        If None, auto-detection is attempted.

    Returns
    -------
    dict
        Structured ingestion metadata:
        {
            "success": bool,
            "source": str,
            "run_id": str,
            "file_name": str,
            "rows": int,
            "columns": [...],
            "schema_hash": str,
            "output_path": str,
            "ingested_at": str,
            "error": str | None,
        }
    """
    path = Path(file_path)

    # ── Validate file exists ──
    if not path.exists():
        msg = f"File not found: {file_path}"
        logger.error(msg)
        return {"success": False, "error": msg}

    # ── Resolve source type ──
    if source_type is None:
        source_type = detect_source_type(file_path)
        if source_type is None:
            msg = (
                f"Cannot auto-detect source type for '{path.name}'. "
                f"Please specify source_type explicitly."
            )
            logger.error(msg)
            return {"success": False, "error": msg}
        logger.info(f"Auto-detected source type: {source_type}")

    source_type = source_type.lower().strip()

    if source_type not in SOURCE_REGISTRY:
        msg = (
            f"Unknown source type: '{source_type}'. "
            f"Valid types: {list(SOURCE_REGISTRY.keys())}"
        )
        logger.error(msg)
        return {"success": False, "error": msg}

    # ── Build ingestor ──
    config = SOURCE_REGISTRY[source_type]
    ingestor_cls = config["ingestor"]

    try:
        if source_type == "operational_excel":
            ingestor = ingestor_cls(
                source_path=file_path,
                output_dir=config["output_dir"],
            )
        else:
            ingestor = ingestor_cls(
                source_path=file_path,
                schema_path=config["schema"],
                output_dir=config["output_dir"],
            )

        logger.info(
            f"Starting ingestion: {path.name} as '{source_type}'"
        )

        # ── Execute ingestion ──
        metadata = ingestor.ingest()

        logger.info(
            f"Ingestion complete: {metadata['rows']} rows, "
            f"run_id={metadata['run_id']}"
        )

        return {
            "success": True,
            "error": None,
            **metadata,
        }

    except Exception as exc:
        msg = f"Ingestion failed for '{path.name}': {exc}"
        logger.error(msg, exc_info=True)
        return {"success": False, "error": msg}
