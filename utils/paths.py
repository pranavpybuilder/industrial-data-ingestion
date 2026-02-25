import os
from pathlib import Path


APP_NAME = "OfflineIndustrialIntelligence"
BASE_DIR = Path(
    os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")
) / APP_NAME

STORAGE_DIR = BASE_DIR / "storage"
LOG_DIR = BASE_DIR / "logs"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
EXPORT_DIR = BASE_DIR / "exports"
MODEL_DIR = BASE_DIR / "models"

for directory in (STORAGE_DIR, LOG_DIR, RAW_DATA_DIR, EXPORT_DIR, MODEL_DIR):
    directory.mkdir(parents=True, exist_ok=True)
