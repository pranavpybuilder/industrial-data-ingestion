@echo off
cd /d "%~dp0"
"venv\Scripts\python.exe" -m PyInstaller frontend/electron_app/main/main.py ^
  --onefile ^
  --windowed ^
  --noconfirm ^
  --icon=app_icon.ico ^
  --add-data "frontend/electron_app/renderer/dist;frontend/electron_app/renderer/dist" ^
  --add-data "storage/schema.sql;storage" ^
  --hidden-import sklearn ^
  --hidden-import scipy ^
  --hidden-import duckdb ^
  --hidden-import pandas ^
  --hidden-import numpy ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --collect-all PySide6 ^
  --collect-all sklearn ^
  --collect-all scipy

echo Build completed. Check dist/ directory.
pause
