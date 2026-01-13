from pathlib import Path
import pandas as pd


class CSVReader:
    """
    Robust CSV reader for industrial data sources.

    Responsibilities:
    - Read CSV files safely
    - Handle encoding, delimiters, and malformed rows
    - Return pandas DataFrame only
    """

    @staticmethod
    def read(
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        low_memory: bool = False,
    ) -> pd.DataFrame:
        """
        Read a CSV file and return a pandas DataFrame.

        Parameters
        ----------
        file_path : str
            Path to the CSV file
        delimiter : str, optional
            Column delimiter (default: ',')
        encoding : str, optional
            File encoding (default: 'utf-8')
        low_memory : bool, optional
            Pandas low_memory flag for large files

        Returns
        -------
        pd.DataFrame
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        try:
            df = pd.read_csv(
                path,
                sep=delimiter,
                encoding=encoding,
                low_memory=low_memory,
                on_bad_lines="skip",   # industrial safety
            )
        except UnicodeDecodeError:
            # Fallback for common industrial encodings
            df = pd.read_csv(
                path,
                sep=delimiter,
                encoding="latin1",
                low_memory=low_memory,
                on_bad_lines="skip",
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to read CSV file {path}: {exc}"
            ) from exc

        # Normalize column names early (very important for ML & rules)
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        return df
