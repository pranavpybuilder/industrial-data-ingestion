"""
File upload handler for ingestion.

Responsibilities:
- Resolve source type (explicit or auto-detected)
- Instantiate source ingestor
- Execute ingestion and return stable metadata contract
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ingestion.sources.generic_tabular_ingestor import GenericTabularIngestor
from ingestion.sources.operational_excel_ingestor import OperationalExcelIngestor
from ingestion.sources.plc_ingestor import PLCIngestor
from ingestion.sources.report_excel_ingestor import ReportExcelIngestor
from ingestion.sources.rfid_ingestor import RFIDIngestor
from ingestion.sources.sap_ingestor import SAPIngestor
from ingestion.readers.excel_reader import ExcelReader
from schema_registry.schema_registry import SchemaRegistry
from utils.logger import get_logger
from utils.paths import RAW_DATA_DIR

logger = get_logger(__name__)
schema_registry = SchemaRegistry()

_CONTRACTS_DIR = Path(__file__).parent / "contracts"

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

_EXTENSION_HINTS: Dict[str, list[str]] = {
    ".csv": ["sap", "energy", "plc", "rfid", "generic_tabular"],
    ".json": ["plc", "rfid"],
    ".xlsx": ["report_excel", "energy", "sap", "generic_tabular", "operational_excel"],
    ".xls": ["report_excel", "energy", "sap", "generic_tabular", "operational_excel"],
    ".log": ["plc"],
    ".txt": ["plc"],
}

SOURCE_TO_SCHEMA_TYPE: Dict[str, str] = {
    "sap": "sap",
    "report_excel": "sap",
    "plc": "plc",
    "rfid": "rfid",
    "energy": "energy",
    "generic_tabular": "generic",
    "operational_excel": "generic",
}


def detect_source_type(file_path: str) -> Optional[str]:
    path = Path(file_path)
    suffix = path.suffix.lower()
    candidates = _EXTENSION_HINTS.get(suffix, [])
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    headers = _preview_headers(path)
    if not headers:
        return "generic_tabular" if "generic_tabular" in candidates else None

    candidate_schemas = sorted(
        {
            SOURCE_TO_SCHEMA_TYPE.get(candidate, "generic")
            for candidate in candidates
        }
    )
    detected_schema = schema_registry.detect_source_from_columns(
        raw_columns=headers,
        candidates=candidate_schemas,
    )
    if detected_schema is None:
        return "generic_tabular" if "generic_tabular" in candidates else None

    return _resolve_source_from_schema(
        detected_schema=detected_schema,
        candidates=candidates,
        file_suffix=suffix,
    )


def _preview_headers(path: Path) -> list[str]:
    try:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(path, nrows=0)
            return [str(c) for c in df.columns]
        if suffix == ".json":
            try:
                df = pd.read_json(path, nrows=20)
            except Exception:
                df = pd.read_json(path, lines=True, nrows=20)
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
    candidates: list[str],
    file_suffix: str,
) -> Optional[str]:
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

    if detected_schema == "generic":
        if "operational_excel" in candidates and file_suffix in (".xlsx", ".xls"):
            return "operational_excel"
        if "generic_tabular" in candidates:
            return "generic_tabular"

    if detected_schema == "energy" and "energy" in candidates:
        return "energy"

    return candidates[0] if candidates else None


def handle_file_upload(
    file_path: str,
    source_type: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {file_path}"
        logger.error(msg)
        return {"success": False, "error": msg}

    if source_type is None:
        source_type = detect_source_type(file_path) or "generic_tabular"
        logger.info("Auto-detected source type: %s", source_type)

    source_type = source_type.lower().strip()
    if source_type not in SOURCE_REGISTRY:
        msg = (
            f"Unknown source type: '{source_type}'. "
            f"Valid types: {sorted(SOURCE_REGISTRY.keys())}"
        )
        logger.error(msg)
        return {"success": False, "error": msg}

    config = SOURCE_REGISTRY[source_type]
    ingestor_cls = config["ingestor"]

    try:
        if source_type in {"generic_tabular", "energy"}:
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
            "Ingestion complete: rows=%s run_id=%s",
            metadata.get("rows", 0),
            metadata.get("run_id"),
        )

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
