from tools.llm_validator import validate_plan_structure, validate_generated_code


def test_validate_plan_good():
    plan = [{"action": "clean", "params": {}}, {"action": "analyze", "params": {}}]
    ok, errs = validate_plan_structure(plan)
    assert ok


def test_validate_plan_bad():
    plan = [{"action": 123}]
    ok, errs = validate_plan_structure(plan)
    assert not ok


def test_validate_code_blacklist():
    bad = "import os\nos.system('rm -rf /')"
    ok, issues = validate_generated_code(bad)
    assert not ok


def test_validate_code_good():
    code = "print('hello')\n"
    ok, issues = validate_generated_code(code)
    assert ok
