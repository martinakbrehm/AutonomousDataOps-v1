import os
import pandas as pd
from agents.data_processing_agent import DataProcessingAgent
from agents.data_quality_agent import DataQualityAgent


def test_data_processing_clean(tmp_path):
    df = pd.DataFrame({"a": [1, 1, 2], "b": [" x ", " x ", "y"]})
    dp = DataProcessingAgent()
    out, info = dp.clean(df)
    assert info["initial_rows"] == 3
    assert info["final_rows"] == 2


def test_data_quality_assess():
    df = pd.DataFrame({"num": [1, 2, None, 4]})
    dq = DataQualityAgent()
    q = dq.assess(df)
    assert q["shape"][0] == 4
    assert "num" in q["missing"]
