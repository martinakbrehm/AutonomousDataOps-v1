import json
from agents.planner_agent import PlannerAgent
from agents.codegen_agent import CodeGenAgent
from tools.external_api import register_provider, APIProvider


class RawResponseProvider(APIProvider):
    def __init__(self, response):
        self._response = response

    async def request(self, path: str, params=None):
        # return raw string or structure depending on test
        return self._response


def test_planner_uses_valid_llm_plan(monkeypatch):
    plan = [{"action": "clean", "params": {}}, {"action": "analyze", "params": {}}]
    provider = RawResponseProvider(json.dumps(plan))
    register_provider('prov_valid', provider)
    planner = PlannerAgent(llm=None)
    # inject LLMAdapter that uses our provider
    from agents.llm_adapter import LLMAdapter
    planner.llm = LLMAdapter(provider_name='prov_valid')

    out = planner.plan({"clean": True})
    assert isinstance(out, list)
    # should match provider plan (not fallback)
    assert out[0]['action'] == 'clean'


def test_planner_fallback_on_malformed_json(monkeypatch):
    provider = RawResponseProvider("not a json")
    register_provider('prov_badjson', provider)
    planner = PlannerAgent(llm=None)
    from agents.llm_adapter import LLMAdapter
    planner.llm = LLMAdapter(provider_name='prov_badjson')

    out = planner.plan({"clean": True})
    # fallback should produce a rule-based plan containing 'clean'
    assert any(s.get('action') == 'clean' for s in out)


def test_planner_fallback_on_invalid_schema(monkeypatch):
    # plan has extra property 'extra' which should violate additionalProperties=False
    bad_plan = [{"action": "clean", "params": {}, "extra": 1}]
    provider = RawResponseProvider(json.dumps(bad_plan))
    register_provider('prov_badschema', provider)
    planner = PlannerAgent(llm=None)
    from agents.llm_adapter import LLMAdapter
    planner.llm = LLMAdapter(provider_name='prov_badschema')

    out = planner.plan({"clean": True})
    # fallback should be used
    assert any(s.get('action') == 'clean' for s in out)


def test_codegen_rejects_forbidden_code():
    cg = CodeGenAgent()
    bad_code = "import os\nos.system('rm -rf /')\n"
    rc, out, err = cg.execute(bad_code)
    assert rc == -2
    assert 'ValidationFailed' in err
