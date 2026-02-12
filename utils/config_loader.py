# utils/config_loader.py

import json
from pathlib import Path
from typing import Dict, Any

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)


def load_yaml(path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"YAML config not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    logger.debug(f"Loaded YAML config: {file_path.name}")
    return data or {}


def load_json(path: str) -> Dict[str, Any]:
    """
    Load a JSON schema or configuration file.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.debug(f"Loaded JSON config: {file_path.name}")
    return data


def resolve_path(*parts: str) -> Path:
    """
    Resolve a path relative to the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    return project_root.joinpath(*parts)
