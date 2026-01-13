from pathlib import Path
import pandas as pd
import json

from ingestion.base_ingestor import BaseIngestor
from ingestion.readers.excel_reader import ExcelReader


class OperationalExcelIngestor(BaseIngestor):
    """
    Ingestor for messy, human-maintained operational Excel files.

    Characteristics:
    - No fixed schema
    - Headers may appear anywhere
    - Multiple tables possible
    - Notes and metadata mixed with data

    Philosophy:
    Ingest first, understand later.
    """

    def __init__(
        self,
        source_path: str,
        output_dir: str = "data/raw/operational_excels",
    ):
        super().__init__(
            source_name="operational_excel",
            source_path=source_path,
            schema_path="",   # schema-less by design (empty string for typing safety)
            output_dir=output_dir,
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def ingest(self) -> dict:
        raw_df = self._read_raw_sheet()
        self._validate_not_empty(raw_df)

        row_profiles = self._profile_rows(raw_df)
        table_regions = self._detect_tables(row_profiles)

        tables = self._extract_tables(raw_df, table_regions)
        metadata = self._extract_metadata(raw_df, table_regions)

        output_paths = self._persist_tables(tables, metadata)

        return {
            "source": self.source_name,
            "run_id": self.run_id,
            "tables_detected": len(tables),
            "output_paths": output_paths,
            "metadata": metadata,
        }

    # ------------------------------------------------------------------
    # Step 1: Read entire sheet with zero assumptions
    # ------------------------------------------------------------------

    def _read_raw_sheet(self) -> pd.DataFrame:
        return ExcelReader.read(
            file_path=str(self.source_path),
            header=None
        )

    # ------------------------------------------------------------------
    # Step 2: Row profiling (heuristics)
    # ------------------------------------------------------------------

    def _profile_rows(self, df: pd.DataFrame) -> list[dict]:
        """
        Profile each row to understand its nature.
        Returns a list of row profile dictionaries.
        """

        profiles: list[dict] = []

        for row_idx in range(len(df)):
            row = df.iloc[row_idx]

            non_null = int(row.notna().sum())
            numeric = int(pd.to_numeric(row, errors="coerce").notna().sum())

            profiles.append(
                {
                    "row_index": row_idx,
                    "non_null_ratio": non_null / max(len(row), 1),
                    "numeric_ratio": numeric / max(non_null, 1),
                }
            )

        return profiles

    # ------------------------------------------------------------------
    # Step 3: Detect table regions
    # ------------------------------------------------------------------

    def _detect_tables(self, profiles: list[dict]) -> list[tuple[int, int]]:
        """
        Detect contiguous table-like row regions.
        """

        table_regions: list[tuple[int, int]] = []
        current_start: int | None = None

        for profile in profiles:
            row_index = profile["row_index"]

            is_table_row = (
                profile["non_null_ratio"] > 0.3
                and profile["numeric_ratio"] > 0.2
            )

            if is_table_row and current_start is None:
                current_start = row_index

            if not is_table_row and current_start is not None:
                table_regions.append((current_start, row_index - 1))
                current_start = None

        if current_start is not None:
            table_regions.append((current_start, profiles[-1]["row_index"]))

        return table_regions

    # ------------------------------------------------------------------
    # Step 4: Extract raw tables
    # ------------------------------------------------------------------

    def _extract_tables(
        self,
        df: pd.DataFrame,
        regions: list[tuple[int, int]],
    ) -> list[dict]:
        tables: list[dict] = []

        for idx, (start, end) in enumerate(regions, start=1):
            table_df = df.iloc[start : end + 1].copy()
            table_df.reset_index(drop=True, inplace=True)

            tables.append(
                {
                    "name": f"table_{idx}_raw",
                    "data": table_df,
                    "row_range": (start, end),
                }
            )

        return tables

    # ------------------------------------------------------------------
    # Step 5: Extract metadata
    # ------------------------------------------------------------------

    def _extract_metadata(
        self,
        df: pd.DataFrame,
        table_regions: list[tuple[int, int]],
    ) -> dict:
        table_rows: set[int] = set()

        for start, end in table_regions:
            table_rows.update(range(start, end + 1))

        metadata_lines: list[str] = []

        for row_idx in range(len(df)):
            if row_idx not in table_rows:
                row_text = " ".join(
                    str(x) for x in df.iloc[row_idx].dropna().tolist()
                )
                if row_text.strip():
                    metadata_lines.append(row_text)

        return {
            "file_name": Path(self.source_path).name,
            "total_rows": int(len(df)),
            "detected_tables": int(len(table_regions)),
            "notes": metadata_lines,
        }

    # ------------------------------------------------------------------
    # Step 6: Persist tables + metadata
    # ------------------------------------------------------------------

    def _persist_tables(
        self,
        tables: list[dict],
        metadata: dict,
    ) -> list[str]:
        run_dir = self.output_dir / f"run_{self.run_id}"
        run_dir.mkdir(parents=True, exist_ok=False)

        output_paths: list[str] = []

        metadata_path = run_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        output_paths.append(str(metadata_path))

        for table in tables:
            table_path = run_dir / f"{table['name']}.parquet"
            table["data"].to_parquet(table_path, index=False)
            output_paths.append(str(table_path))

        return output_paths