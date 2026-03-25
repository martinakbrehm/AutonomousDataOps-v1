import os
from pipelines.etl_pipeline import run_pipeline_from_file


def test_run_pipeline(tmp_path):
    # copy example csv to temp
    src = os.path.join(os.path.dirname(__file__), '..', 'example_data', 'sample.csv')
    dst = tmp_path / 'sample.csv'
    with open(src, 'r', encoding='utf-8') as fr, open(dst, 'w', encoding='utf-8') as fw:
        fw.write(fr.read())
    df, summary = run_pipeline_from_file(str(dst), {"clean": True, "analyze": True, "transform": False})
    assert summary["rows"] <= 4
