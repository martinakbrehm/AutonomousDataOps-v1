import pandas as pd
from typing import Dict, Any


class DataQualityAgent:
    def __init__(self, memory=None):
        self.memory = memory

    def assess(self, df: pd.DataFrame) -> Dict[str, Any]:
        q = {}
        q["shape"] = df.shape
        q["missing"] = df.isna().sum().to_dict()
        # simple anomaly detection: z-score for numeric columns
        from scipy import stats
        numerics = df.select_dtypes(include=["number"]).columns
        anomalies = {}
        for c in numerics:
            col = df[c].dropna()
            if len(col) > 1:
                z = stats.zscore(col)
                anomalies[c] = int((abs(z) > 3).sum())
        q["anomalies"] = anomalies
        if self.memory:
            # record issues
            for c, cnt in q["missing"].items():
                if cnt > 0:
                    self.memory.add_issue(source=c, detail=f"{cnt} missing values", severity="low")
        return q
