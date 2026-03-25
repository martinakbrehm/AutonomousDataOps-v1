import pandas as pd
from typing import Tuple


class DataProcessingAgent:
    def __init__(self, memory=None):
        self.memory = memory

    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        info = {"initial_rows": len(df)}
        # Basic cleaning: drop exact duplicates, strip whitespace from strings
        df = df.copy()
        df = df.drop_duplicates()
        for c in df.select_dtypes(include=[object]).columns:
            df[c] = df[c].str.strip()
        # fill trivial missing numeric with median
        for c in df.select_dtypes(include=["number"]).columns:
            if df[c].isna().any():
                df[c] = df[c].fillna(df[c].median())
        info["final_rows"] = len(df)
        return df, info

    def transform(self, df: pd.DataFrame, params: dict) -> Tuple[pd.DataFrame, dict]:
        df = df.copy()
        ops = params.get("ops", [])
        details = {}
        for op in ops:
            if op.get("type") == "drop_columns":
                cols = op.get("columns", [])
                df = df.drop(columns=[c for c in cols if c in df.columns])
                details["dropped"] = cols
        return df, details
