import os
import json
from pipelines.etl_pipeline import build_default_system
from tools.external_api import register_provider, APIProvider


class CountingMockProvider(APIProvider):
    def __init__(self, response):
        self._response = response
        self.calls = 0

    async def request(self, path: str, params=None):
        self.calls += 1
        return self._response


def test_pipeline_with_mock_llm(tmp_path, monkeypatch):
    # prepare CSV
    src = os.path.join(os.path.dirname(__file__), 'example_data', 'sample.csv')
    dst = tmp_path / 'sample.csv'
    with open(src, 'r', encoding='utf-8') as fr, open(dst, 'w', encoding='utf-8') as fw:
        fw.write(fr.read())

    # build system with isolated memory paths
    mem_path = str(tmp_path / 'mem.db')
    vec_path = str(tmp_path / 'vec')
    orch = build_default_system(mem_path=mem_path, vec_path=vec_path)

    # register a provider that returns a valid JSON plan
    plan = [{"action": "clean", "params": {}}, {"action": "analyze", "params": {}}]
    provider_resp = json.dumps(plan)
    provider = CountingMockProvider(provider_resp)
    register_provider('testmock', provider)

    # force planner to use our provider
    from agents.llm_adapter import LLMAdapter
    orch.planner.llm = LLMAdapter(provider_name='testmock')

    # run pipeline
    from tools.file_io import read_dataset
    df = read_dataset(str(dst))
    req = {"clean": True, "analyze": True}
    plan_out = orch.planner.plan(req)
    assert isinstance(plan_out, list) and len(plan_out) >= 1
    result_df, summary = orch.run_plan(plan_out, df)

    # SQLMemory should have logs for steps and insight
    logs = orch.memory_sql.query_logs()
    assert any('data_agent' in row for row in [r[1] for r in logs])
    assert 'rows' in summary


def test_llm_adapter_cache_behavior(monkeypatch):
    # provider that counts calls
    class SimpleProvider(APIProvider):
        def __init__(self):
            self.calls = 0

        async def request(self, path: str, params=None):
            self.calls += 1
            return {"text": "[PLAN] []"}

    prov = SimpleProvider()
    register_provider('countprov', prov)

    from agents.llm_adapter import LLMAdapter
    import asyncio

    llm = LLMAdapter(provider_name='countprov')
    prompt = "Test prompt"
    # first call
    out1 = llm.generate(prompt)
    # second call should hit cache
    out2 = llm.generate(prompt)
    assert out1 == out2
    assert prov.calls == 1
