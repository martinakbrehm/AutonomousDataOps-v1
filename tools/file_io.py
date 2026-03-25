import pandas as pd
from typing import Tuple


def read_dataset(path: str) -> pd.DataFrame:
    if path.lower().endswith((".csv", ".txt")):
        return pd.read_csv(path)
    if path.lower().endswith(('.xls', '.xlsx')):
        return pd.read_excel(path)
    raise ValueError("Unsupported file format")


def write_dataset(df: pd.DataFrame, path: str) -> None:
    if path.lower().endswith('.csv'):
        df.to_csv(path, index=False)
    elif path.lower().endswith(('.xls', '.xlsx')):
        df.to_excel(path, index=False)
    else:
        raise ValueError("Unsupported file format for write")
