from typing import List, Dict, Any
from datetime import datetime


class IngestionManager:
    """
    Orchestrates execution of multiple data ingestors.

    Supports:
    - Strict mode (fail fast)
    - Tolerant mode (continue on error)
    - Structured run summaries for audit & ML lineage
    """

    def __init__(
        self,
        ingestors: List[Any],
        strict: bool = True,
    ):
        """
        Parameters
        ----------
        ingestors : list
            List of instantiated ingestor objects
        strict : bool
            If True, stop on first failure.
            If False, continue ingestion and collect errors.
        """
        self.ingestors = ingestors
        self.strict = strict

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute ingestion for all configured ingestors.

        Returns
        -------
        dict
            Structured summary of ingestion run
        """

        run_started_at = datetime.utcnow().isoformat()

        results = []
        errors = []

        for ingestor in self.ingestors:
            try:
                metadata = ingestor.ingest()
                results.append(metadata)
            except Exception as exc:
                error_info = {
                    "source": getattr(ingestor, "source_name", "unknown"),
                    "error": str(exc),
                }
                errors.append(error_info)

                if self.strict:
                    raise RuntimeError(
                        f"Ingestion failed for source "
                        f"{error_info['source']}: {error_info['error']}"
                    ) from exc

        return {
            "run_started_at": run_started_at,
            "run_finished_at": datetime.utcnow().isoformat(),
            "strict_mode": self.strict,
            "successful_sources": results,
            "failed_sources": errors,
        }