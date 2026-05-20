"""Layer 4 sandboxed SymPy worker.

Purpose: run symbolic checks outside the FastAPI event loop in a bounded
process pool. Constraints: `SYMPY_MAX_WORKERS` must cap workers, each task has
a hard timeout, and timeouts must trigger conceptual fallback instead of
hanging requests.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, TimeoutError
from functools import lru_cache
from typing import Any

from app.core.config import get_settings


def execute_sympy_verification(task_name: str, payload: dict[str, Any]) -> Any:
    """Execute a bounded symbolic task outside the request process."""
    settings = get_settings()
    future = _get_executor().submit(_run_sympy_task, task_name, payload)
    try:
        return future.result(timeout=settings.sympy_timeout_ms / 1000)
    except TimeoutError as exc:
        future.cancel()
        raise TimeoutError("SymPy verification timed out") from exc


@lru_cache(maxsize=1)
def _get_executor() -> ProcessPoolExecutor:
    return ProcessPoolExecutor(max_workers=get_settings().sympy_max_workers)


def _run_sympy_task(task_name: str, payload: dict[str, Any]) -> Any:
    from sympy import Eq, factor, solve, symbols
    from sympy.parsing.sympy_parser import parse_expr

    x = symbols("x")
    if task_name == "factor_and_solve_zero":
        expression = parse_expr(payload["expression"], local_dict={"x": x})
        return {
            "factorized": str(factor(expression)),
            "roots": [str(root) for root in solve(Eq(expression, 0), x)],
        }

    raise ValueError(f"Unsupported SymPy task: {task_name}")
