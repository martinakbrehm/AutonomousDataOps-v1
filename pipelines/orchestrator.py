import time
from typing import Any, Dict
from utils.logging_config import logger
from utils.observability import trace_span, STEP_DURATION


def retry(max_retries=2, backoff=1.0):
    def deco(fn):
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 2):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    logger.warning(f"Attempt {attempt} failed: {e}")
                    time.sleep(backoff * attempt)
            raise last_exc
        return wrapper
    return deco


class Orchestrator:
    def __init__(self, planner, data_agent, quality_agent, code_agent, insight_agent, memory_sql=None, memory_vec=None):
        self.planner = planner
        self.data_agent = data_agent
        self.quality_agent = quality_agent
        self.codegen = code_agent
        self.insight = insight_agent
        self.memory_sql = memory_sql
        self.memory_vec = memory_vec

    def trace(self, agent: str, action: str, detail: str):
        if self.memory_sql:
            self.memory_sql.log(agent, action, detail)
        logger.info(f"TRACE {agent}:{action} - {detail}")

    def _timed_step(self, agent: str, action: str, fn, *args, **kwargs):
        with trace_span(f"{agent}.{action}"):
            start = time.time()
            res = fn(*args, **kwargs)
            elapsed = time.time() - start
            try:
                STEP_DURATION.labels(agent=agent, action=action).observe(elapsed)
            except Exception:
                pass
            return res

    @retry(max_retries=1, backoff=0.5)
    def run_step(self, step: Dict[str, Any], df=None):
        action = step.get("action")
        params = step.get("params", {})
        self.trace("planner", "execute_step", action)
        if action == "inspect_memory":
            # no-op other than logging
            self.trace("planner", "memory_hints", str(params.get("hints")))
            return df
        if action == "clean":
            df2, info = self.data_agent.clean(df)
            self.trace("data_agent", "clean", str(info))
            return df2
        if action == "analyze":
            q = self.quality_agent.assess(df)
            self.trace("quality_agent", "assess", str(q))
            return df
        if action == "transform":
            df2, info = self.data_agent.transform(df, params)
            self.trace("data_agent", "transform", str(info))
            return df2
        raise RuntimeError(f"Unknown action {action}")

    def run_plan(self, plan, df):
        current = df
        for step in plan:
            try:
                # run each step with timing and tracing
                current = self._timed_step("orchestrator", step.get("action"), self.run_step, step, df=current)
            except Exception as e:
                self.trace("orchestrator", "step_error", f"{step} -> {e}")
                if self.memory_sql:
                    self.memory_sql.add_issue(source=step.get("action"), detail=str(e), severity="high")
        # final insight
        summary = self.insight.summarize(current)
        self.trace("insight_agent", "summary", str({"rows": summary.get('rows')}))
        return current, summary
