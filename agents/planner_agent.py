from typing import List, Dict, Any, Optional

from .llm_adapter import LLMAdapter


class PlannerAgent:
    """Derives a sequence of high-level steps from user intent or dataset metadata.

    Uses an LLM via `LLMAdapter` when available; falls back to a rule-based planner.
    """

    def __init__(self, memory=None, llm: Optional[LLMAdapter] = None):
        self.memory = memory
        self.llm = llm or LLMAdapter()

    def plan(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        # prefer LLM-generated plan when available
        if self.llm and self.llm.is_available():
            prompt = f"Generate a JSON array of steps for the request: {request}"
            try:
                out = self.llm.generate(prompt)
                # naive parsing: expect JSON-like string
                import json
                from tools.llm_validator import validate_plan_structure

                parsed = json.loads(out)
                ok, errs = validate_plan_structure(parsed)
                if ok:
                    return parsed
                # if invalid, fall through to rule-based planner
            except Exception:
                pass

        # Rule-based fallback planner
        steps: List[Dict[str, Any]] = []
        if request.get("clean"):
            steps.append({"action": "clean", "params": {}})
        if request.get("analyze"):
            steps.append({"action": "analyze", "params": {}})
        if request.get("transform"):
            steps.append({"action": "transform", "params": request.get("transform_params", {})})
        # consult memory for known issues or rules
        if self.memory and hasattr(self.memory, 'query'):
            try:
                hints = self.memory.query("recent issues", k=3)
                if hints:
                    steps.insert(0, {"action": "inspect_memory", "params": {"hints": hints}})
            except Exception:
                pass
        return steps
