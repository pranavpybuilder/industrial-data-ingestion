from pathlib import Path
import pandas as pd


class ExcelReader:
    """
    Robust Excel reader for industrial maintenance data.

    Handles:
    - Multiple sheets
    - Non-header first rows
    - Empty / merged rows
    - Column normalization
    """

    @staticmethod
    def read(
        file_path: str,
        sheet_name: str | int = 0,
        header: int | None = 0,
    ) -> pd.DataFrame:
        """
        Read an Excel file and return a pandas DataFrame.

        Parameters
        ----------
        file_path : str
            Path to Excel file
        sheet_name : str | int, optional
            Sheet name or index (default: first sheet)
        header : int | None, optional
            Row number to use as header.
            Use None if headers are not defined.

        Returns
        -------
        pd.DataFrame
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            # Allow CSV files to be read through the Excel reader path
            try:
                df = pd.read_csv(str(path), header=header)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to read CSV file {path}: {exc}"
                ) from exc
        elif suffix in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(
                    str(path),
                    sheet_name=sheet_name,
                    header=header,
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to read Excel file {path}: {exc}"
                ) from exc
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. Expected .xlsx, .xls, or .csv"
            )

        # Drop completely empty rows (very common in industrial files)
        df = df.dropna(how="all")

        # Normalize column names if headers exist
        if header is not None:
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