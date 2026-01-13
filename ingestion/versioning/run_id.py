from datetime import datetime
import uuid


def generate_run_id() -> str:
    """
    Generate a unique, human-readable ingestion run ID.

    Format:
        YYYYMMDD_HHMMSS_<8-char-uuid>

    Example:
        20260110_113245_a9f3c2d1
    """

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]

    return f"{timestamp}_{short_uuid}"
