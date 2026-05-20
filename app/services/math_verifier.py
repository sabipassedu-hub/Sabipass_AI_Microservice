"""SymPy-backed math grounding for tutor responses."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from sympy import Eq, factor, solve, symbols
from sympy.parsing.sympy_parser import parse_expr

from app.math.normalizer import normalize_math_input


MathVerificationStatus = Literal["verified", "conceptual", "unsupported"]


@dataclass(frozen=True)
class MathVerificationResult:
    status: MathVerificationStatus
    source: str
    response_text: str | None = None
    prompt_context: str = ""


def verify_math_request(raw_input: str, *, concept_key: str | None) -> MathVerificationResult:
    """Return deterministic math grounding when the current input is supported."""
    normalized = normalize_math_input(raw_input)

    if concept_key == "surds" or "surd" in normalized:
        return _surds_grounding()

    if concept_key == "quadratic_equations" or _looks_quadratic(normalized):
        result = _quadratic_grounding(normalized)
        if result is not None:
            return result

    return MathVerificationResult(
        status="unsupported",
        source="none",
        prompt_context="No deterministic math verification was available.",
    )


def _surds_grounding() -> MathVerificationResult:
    text = (
        "Surds are irrational roots that cannot simplify to rational numbers. "
        "For example, sqrt(2), sqrt(3), and 2sqrt(5) are surds. "
        "sqrt(4) is not a surd because it simplifies to 2. "
        "Pi is irrational, but it is not a surd because it is not written as an "
        "unresolved root of a rational number."
    )
    return MathVerificationResult(
        status="conceptual",
        source="sympy_rulebook",
        response_text=(
            "Surds are roots that cannot simplify to rational numbers. "
            "For example, sqrt(2) and sqrt(3) are surds, but sqrt(4) is not, "
            "because sqrt(4) = 2. Pi is irrational, but it is not a surd."
        ),
        prompt_context=text,
    )


def _quadratic_grounding(normalized: str) -> MathVerificationResult | None:
    expression_text = _extract_expression(normalized)
    if expression_text is None:
        return None

    try:
        x = symbols("x")
        expression = parse_expr(expression_text, local_dict={"x": x})
        factorized = factor(expression)
        roots = solve(Eq(expression, 0), x)
    except Exception:
        return None

    roots_text = ", ".join(str(root) for root in roots)
    prompt_context = (
        f"SymPy verified expression={expression}; factorized={factorized}; "
        f"roots_if_equal_zero={roots_text}."
    )
    return MathVerificationResult(
        status="verified",
        source="sympy",
        response_text=(
            f"Treat the expression as equal to zero: {expression} = 0. "
            f"It factorises as {factorized} = 0, so the solutions are x = {roots_text}."
        ),
        prompt_context=prompt_context,
    )


def _looks_quadratic(normalized: str) -> bool:
    return "x**2" in normalized or bool(re.search(r"\bx\^2\b", normalized))


def _extract_expression(normalized: str) -> str | None:
    selected = normalized
    for prefix in ("solve", "factorise", "factorize", "factor"):
        if selected.startswith(prefix + " "):
            selected = selected[len(prefix) + 1 :]
            break

    if "=" in selected:
        left, right = selected.split("=", 1)
        selected = f"({left})-({right})"

    selected = re.sub(r"[^x0-9+\-*/(). ]+", " ", selected)
    selected = " ".join(selected.split())
    return selected or None
