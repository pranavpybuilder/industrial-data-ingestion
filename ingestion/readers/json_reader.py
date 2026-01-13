from pathlib import Path
import pandas as pd


class JSONReader:
    """
    Robust JSON reader for industrial data ingestion.

    Handles:
    - Standard JSON files
    - Line-delimited JSON (auto-detected)
    """

    @staticmethod
    def read(file_path: str) -> pd.DataFrame:
        """
        Read a JSON file and return a pandas DataFrame.

        Parameters
        ----------
        file_path : str
            Path to JSON file

        Returns
        -------
        pd.DataFrame
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")

        if path.suffix.lower() != ".json":
            raise ValueError(
                f"Unsupported JSON format: {path.suffix}"
            )

        try:
            # Let pandas infer orient and lines automatically
            df = pd.read_json(str(path))
        except ValueError:
            # Fallback for line-delimited JSON
            df = pd.read_json(str(path), lines=True)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to read JSON file {path}: {exc}"
            ) from exc

        # Drop completely empty rows
        df = df.dropna(how="all")

        # Normalize column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
        )

        df.reset_index(drop=True, inplace=True)
        return df