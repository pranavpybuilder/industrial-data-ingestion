# utils/logger.py

import logging
import sys
from pathlib import Path
from datetime import datetime


_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_INITIALIZED_LOGGERS = set()


def get_logger(name: str = "industrial") -> logging.Logger:
    """
    Returns a configured logger instance.

    - Console output (INFO+)
    - File output (DEBUG+) to logs/app_YYYYMMDD.log
    - Single initialization per logger name
    """
    global _INITIALIZED_LOGGERS

    logger = logging.getLogger(name)

    # Skip if this logger was already initialized
    if name in _INITIALIZED_LOGGERS:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(
        _LOG_DIR / log_filename,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _INITIALIZED_LOGGERS.add(name)
    return logger
