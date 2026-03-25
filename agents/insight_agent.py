from typing import Any, Dict
import pandas as pd


class InsightAgent:
    def __init__(self, memory=None):
        self.memory = memory

    def summarize(self, df: pd.DataFrame) -> Dict[str, Any]:
        s = {}
        s["rows"] = len(df)
        s["columns"] = list(df.columns)
        s["dtypes"] = {c: str(dt) for c, dt in df.dtypes.items()}
        s["basic_stats"] = df.describe(include='all').to_dict()
        # store summary to memory
        if self.memory:
            self.memory.add({"type": "summary", "summary": s})
        return s
