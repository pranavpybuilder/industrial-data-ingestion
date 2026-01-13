from pathlib import Path
import pandas as pd
import re


class LogReader:
    """
    Robust reader for industrial log files (PLC / machine / system logs).

    Handles:
    - Plain text log files
    - Timestamp extraction (multiple formats)
    - Noisy / banner lines
    - Structured DataFrame output
    """

    # Common timestamp patterns seen in industrial logs
    TIMESTAMP_PATTERNS = [
        r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}",      # 2026-01-10 11:23:45
        r"\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2}",      # 10/01/2026 11:23:45
        r"\d{2}-\d{2}-\d{4}[ T]\d{2}:\d{2}:\d{2}"       # 10-01-2026 11:23:45
    ]

    @staticmethod
    def read(file_path: str) -> pd.DataFrame:
        """
        Read a log file and return a pandas DataFrame.

        Output columns:
        - event_time (nullable)
        - message
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {path}")

        if path.suffix.lower() not in [".log", ".txt"]:
            raise ValueError(
                f"Unsupported log file format: {path.suffix}"
            )

        records = []

        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                event_time = LogReader._extract_timestamp(line)
                message = LogReader._strip_timestamp(line)

                records.append(
                    {
                        "event_time": event_time,
                        "message": message,
                    }
                )

        if not records:
            raise ValueError("Log file contains no readable events")

        df = pd.DataFrame(records)

        # Normalize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

        return df

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_timestamp(line: str):
        """
        Extract timestamp from a log line if present.
        Returns None if no timestamp found.
        """
        for pattern in LogReader.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def _strip_timestamp(line: str) -> str:
        """
        Remove timestamp from log line to extract message.
        """
        for pattern in LogReader.TIMESTAMP_PATTERNS:
            line = re.sub(pattern, "", line)
        return line.strip()
