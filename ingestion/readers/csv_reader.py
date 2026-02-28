"""
Robust CSV reader for industrial data sources.

Features:
- Multi-encoding fallback cascade (utf-8-sig, utf-8, latin-1, windows-1252, cp1252)
- Multi-delimiter auto-detection (comma, semicolon, tab, pipe)
- Bad line skip for messy industrial exports
- Column normalization (lowercase, underscores, strip special chars)
- Never crashes the app — always returns a usable DataFrame or raises IngestionError

Tested against: Breakdown_data.csv (Plant 1152, 46 columns, 57 rows, maintenance domain)
"""

from pathlib import Path
from typing import Optional

import pandas as pd


class IngestionError(Exception):
    """Raised when CSV ingestion fails after exhausting all fallback strategies."""


class CSVReader:
    """
    Robust CSV reader for industrial data sources.

    Tries multiple encodings and delimiters until a valid parse is found.
    A valid parse is defined as >= 2 columns and >= 1 data row.
    """

    ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "windows-1252", "cp1252"]
    DELIMITERS = [",", ";", "\t", "|"]

    @staticmethod
    def read(
        file_path: str,
        delimiter: Optional[str] = None,
        encoding: Optional[str] = None,
        low_memory: bool = False,
        normalize_columns: bool = True,
    ) -> pd.DataFrame:
        """
        Read a CSV file with robust encoding and delimiter detection.

        Parameters
        ----------
        file_path : str
            Path to the CSV file.
        delimiter : str, optional
            If provided, only this delimiter is tried. Otherwise auto-detect.
        encoding : str, optional
            If provided, only this encoding is tried. Otherwise auto-detect.
        low_memory : bool
            Pandas low_memory flag for large files.
        normalize_columns : bool
            If True, normalize column names to lowercase with underscores.

        Returns
        -------
        pd.DataFrame
            Parsed DataFrame with at least 2 columns and 1 row.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        IngestionError
            If the file cannot be parsed after all fallback attempts.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        encodings_to_try = [encoding] if encoding else CSVReader.ENCODINGS
        delimiters_to_try = [delimiter] if delimiter else CSVReader.DELIMITERS

        last_error: Optional[Exception] = None

        for enc in encodings_to_try:
            for delim in delimiters_to_try:
                try:
                    df = pd.read_csv(
                        path,
                        sep=delim,
                        encoding=enc,
                        dtype=str,
                        on_bad_lines="skip",
                        skip_blank_lines=True,
                        low_memory=low_memory,
                    )
                    # A valid parse has at least 2 columns and 1 data row
                    if df.shape[1] >= 2 and df.shape[0] >= 1:
                        # Drop fully-empty rows and columns
                        df = df.dropna(how="all").dropna(axis=1, how="all")
                        df = df.reset_index(drop=True)

                        if df.shape[1] >= 2 and df.shape[0] >= 1:
                            if normalize_columns:
                                df.columns = CSVReader._normalize_columns(df.columns)
                            return df
                except Exception as exc:
                    last_error = exc
                    continue

        raise IngestionError(
            f"Cannot parse CSV: {path}. "
            f"Tried encodings {encodings_to_try} × delimiters {[repr(d) for d in delimiters_to_try]}. "
            f"Last error: {last_error}"
        )

    @staticmethod
    def _normalize_columns(columns: pd.Index) -> pd.Index:
        """
        Normalize column names: strip whitespace, lowercase,
        replace spaces and special chars with underscores.
        """
        normalized = (
            columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
            .str.replace("/", "_")
            .str.replace(r"[^a-z0-9_]+", "", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )

        # Deduplicate column names by appending _2, _3, etc.
        seen: dict[str, int] = {}
        deduped: list[str] = []
        for name in normalized:
            if name in seen:
                seen[name] += 1
                deduped.append(f"{name}_{seen[name]}")
            else:
                seen[name] = 1
                deduped.append(name)

        return pd.Index(deduped)
