from typing import Any, Dict

import pandas as pd

from storage.repositories.ingestion_repo import IngestionRepository
from storage.repositories.run_repo import RunRepository

ingestion_repo = IngestionRepository()
run_repo = RunRepository()


def get_explorer_data_ipc(run_id: str, limit: int = 500) -> Dict[str, Any]:
    if not run_id:
        return {"success": False, "data": None, "message": "Run ID is required"}

    run = run_repo.get_run(run_id)
    if run is None:
        return {"success": False, "data": None, "message": "Run not found"}

    if str(run.get("status", "")).upper() == "FAILED":
        return {
            "success": False,
            "data": None,
            "message": (
                f"Run failed at '{run.get('failed_step') or 'unknown'}': "
                f"{run.get('error_message') or 'No error message recorded'}"
            ),
        }

    output_path = ingestion_repo.get_latest_output_path(run_id)
    if not output_path:
        return {
            "success": False,
            "data": None,
            "message": "No ingested dataset found for run",
        }

    df = pd.read_parquet(output_path)
    if df.empty:
        return {
            "success": True,
            "data": {"columns": [], "rows": []},
            "message": "Dataset is empty",
        }

    safe_limit = max(1, min(int(limit), 5000))
    sampled = df.head(safe_limit).copy()

    for col in sampled.columns:
        if pd.api.types.is_datetime64_any_dtype(sampled[col]):
            sampled[col] = sampled[col].astype(str)

    rows = sampled.where(pd.notnull(sampled), None).to_dict(orient="records")
    return {
        "success": True,
        "data": {
            "columns": list(sampled.columns),
            "rows": rows,
            "row_count": int(len(df)),
            "sample_size": int(len(sampled)),
        },
        "message": f"Loaded {len(sampled)} of {len(df)} rows",
    }
