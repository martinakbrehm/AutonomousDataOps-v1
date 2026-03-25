from typing import Tuple
from tools.executor import execute_python_in_venv
from tools.llm_validator import validate_generated_code
import logging

logger = logging.getLogger('autodops.codegen')


class CodeGenAgent:
    def __init__(self, memory=None):
        self.memory = memory

    def generate_cleaning_code(self, sample_head_csv: str) -> str:
        # In production, call an LLM to generate code; here we template a safe routine
        code = f"""
import pandas as pd
df = pd.read_csv(r'{sample_head_csv}')
df = df.drop_duplicates()
for c in df.select_dtypes(include=['object']).columns:
    df[c] = df[c].str.strip()
print('ROWS', len(df))
df.to_csv('generated_cleaned.csv', index=False)
"""
        return code

    def execute(self, code: str, timeout: int = 10) -> Tuple[int, str, str]:
        # Validate generated code before executing
        ok, issues = validate_generated_code(code)
        if not ok:
            logger.warning(f"Code validation failed: {issues}")
            return -2, "", f"ValidationFailed: {issues}"
        # Use venv-based execution for better isolation
        return execute_python_in_venv(code, timeout=timeout)
