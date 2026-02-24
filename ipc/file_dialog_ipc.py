from pathlib import Path
from typing import Any, Dict

from PySide6.QtWidgets import QFileDialog


def select_file_ipc() -> Dict[str, Any]:
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select data file",
        "",
        "Data Files (*.csv *.xlsx *.xls *.json *.log *.txt);;All Files (*)",
    )

    if not file_path:
        return {
            "success": False,
            "data": None,
            "message": "No file selected",
        }

    path = Path(file_path)
    return {
        "success": True,
        "data": {
            "file_path": str(path),
            "file_name": path.name,
            "extension": path.suffix.lower(),
        },
        "message": f"Selected {path.name}",
    }


def select_directory_ipc() -> Dict[str, Any]:
    directory = QFileDialog.getExistingDirectory(
        None,
        "Select export folder",
        "",
    )

    if not directory:
        return {
            "success": False,
            "data": None,
            "message": "No directory selected",
        }

    path = Path(directory)
    return {
        "success": True,
        "data": {
            "directory_path": str(path),
            "directory_name": path.name,
        },
        "message": f"Selected export folder: {path}",
    }
