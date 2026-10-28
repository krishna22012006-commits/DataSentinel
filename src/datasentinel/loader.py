"""Load datasets from CSV or Excel (paths or uploaded file objects)."""
from pathlib import Path

import pandas as pd

SUPPORTED = {".csv", ".xlsx", ".xls"}


def load_dataset(source, filename: str | None = None) -> pd.DataFrame:
    """Load a CSV/Excel file from a path or a file-like object."""
    is_path = isinstance(source, (str, Path))
    name = filename or (str(source) if is_path else getattr(source, "name", ""))
    suffix = Path(name).suffix.lower()

    if is_path and not Path(source).exists():
        raise FileNotFoundError(f"Dataset not found: {source}")
    if suffix not in SUPPORTED:
        raise ValueError("Unsupported file type. Use .csv, .xlsx or .xls")
    try:
        df = pd.read_csv(source) if suffix == ".csv" else pd.read_excel(source)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError("The file has an invalid format.") from exc
    if df.empty:
        raise ValueError("The file contains no data rows.")
    return df


load_csv = load_dataset  # backwards-compatible alias
