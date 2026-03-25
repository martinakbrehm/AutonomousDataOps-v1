from agents.planner_agent import PlannerAgent
from agents.data_processing_agent import DataProcessingAgent
from agents.data_quality_agent import DataQualityAgent
from agents.codegen_agent import CodeGenAgent
from agents.insight_agent import InsightAgent
from memory.sql_memory import SQLMemory
from memory.vector_store import VectorStore
from pipelines.orchestrator import Orchestrator
from tools.file_io import read_dataset
from utils.logging_config import logger


def build_default_system(mem_path='.memory.db', vec_path='.vectordb'):
    sql_mem = SQLMemory(mem_path)
    vec = VectorStore(persist_dir=vec_path)
    planner = PlannerAgent(memory=vec)
    dp = DataProcessingAgent(memory=sql_mem)
    dq = DataQualityAgent(memory=sql_mem)
    cg = CodeGenAgent(memory=vec)
    insight = InsightAgent(memory=vec)
    orch = Orchestrator(planner, dp, dq, cg, insight, memory_sql=sql_mem, memory_vec=vec)
    return orch


def run_pipeline_from_file(path: str, request: dict):
    orch = build_default_system()
    df = read_dataset(path)
    plan = orch.planner.plan(request)
    logger.info(f"Plan: {plan}")
    result_df, summary = orch.run_plan(plan, df)
    return result_df, summary
