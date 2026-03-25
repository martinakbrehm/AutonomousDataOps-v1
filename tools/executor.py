import subprocess
import tempfile
import os
import shlex
import venv
from typing import Tuple


def execute_python_subprocess(code: str, timeout: int = 10) -> Tuple[int, str, str]:
    """Legacy subprocess execution (no venv)."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "run.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        cmd = f"python {shlex.quote(path)}"
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=timeout)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            proc.kill()
            return -1, "", "TimeoutExpired"


def execute_python_in_venv(code: str, timeout: int = 20) -> Tuple[int, str, str]:
    """Execute provided Python code inside a fresh virtualenv for isolation.

    This creates a temporary venv, writes `run.py`, and runs it with the venv python.
    Note: creating venvs per-job has overhead; acceptable for testing and per-user isolation.
    """
    with tempfile.TemporaryDirectory() as d:
        venv_dir = os.path.join(d, "venv")
        venv.create(venv_dir, with_pip=False)
        py = os.path.join(venv_dir, "Scripts" if os.name == "nt" else "bin", "python")
        path = os.path.join(d, "run.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        cmd = [py, path]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=timeout)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            proc.kill()
            return -1, "", "TimeoutExpired"

