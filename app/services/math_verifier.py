"""SymPy-backed math grounding for tutor responses."""

from __future__ import annotations

import re
from concurrent.futures import TimeoutError as SymPyTimeoutError
from dataclasses import dataclass
from typing import Literal

from app.math.normalizer import normalize_math_input
from app.math.sympy_worker import execute_sympy_verification


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

    if concept_key == "surds" or "surd" in normalized or "sqrt" in normalized:
        return _surd_grounding(normalized)

    if concept_key == "quadratic_equations" or _looks_quadratic(normalized):
        result = _quadratic_grounding(normalized)
        if result is not None:
            return result
        return _quadratic_conceptual_grounding()

    if concept_key == "linear_equations" or _looks_linear_equation(normalized):
        result = _linear_equation_grounding(normalized)
        if result is not None:
            return result
        return _linear_conceptual_grounding()

    if concept_key == "algebra":
        return _algebra_conceptual_grounding()

    if concept_key == "general_mathematics":
        return _general_math_grounding()

    return MathVerificationResult(
        status="unsupported",
        source="none",
        prompt_context="No deterministic math verification was available.",
    )


def _surd_grounding(normalized: str) -> MathVerificationResult:
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
        verification = execute_sympy_verification(
            "factor_and_solve_zero",
            {"expression": expression_text},
        )
    except SymPyTimeoutError:
        return _quadratic_timeout_fallback(expression_text)
    except Exception:
        return None

    expression = verification["expression"]
    factorized = verification["factorized"]
    roots_text = ", ".join(verification["roots"])
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


def _linear_equation_grounding(normalized: str) -> MathVerificationResult | None:
    expression_text = _extract_expression(normalized)
    if expression_text is None:
        return None

    try:
        verification = execute_sympy_verification(
            "factor_and_solve_zero",
            {"expression": expression_text},
        )
    except SymPyTimeoutError:
        return MathVerificationResult(
            status="conceptual",
            source="sympy_timeout",
            response_text=(
                "This looks like a linear equation, but I could not verify the "
                "exact value quickly. Collect the x terms on one side, move the "
                "constants to the other side, then divide by the coefficient of x."
            ),
            prompt_context=(
                f"SymPy timed out before solving expression={expression_text}. "
                "Use conceptual linear-equation guidance only."
            ),
        )
    except Exception:
        return None

    roots = verification["roots"]
    if len(roots) != 1:
        return None

    expression = verification["expression"]
    root = roots[0]
    prompt_context = f"SymPy verified expression={expression}; root_if_equal_zero={root}."
    return MathVerificationResult(
        status="verified",
        source="sympy",
        response_text=(
            f"Rewrite the equation as {expression} = 0. Move the constant terms "
            f"away from x, then divide by the coefficient of x. The solution is "
            f"x = {root}; check it by substituting {root} back into the original equation."
        ),
        prompt_context=prompt_context,
    )


def _quadratic_timeout_fallback(expression_text: str) -> MathVerificationResult:
    prompt_context = (
        f"SymPy timed out before verifying expression={expression_text}. "
        "Use conceptual quadratic-solving guidance only; do not claim exact roots."
    )
    return MathVerificationResult(
        status="conceptual",
        source="sympy_timeout",
        response_text=(
            "This looks like a quadratic, but I could not verify the exact factors "
            "quickly. Put it in ax^2 + bx + c = 0 form, then either factor by "
            "finding two numbers that multiply to ac and add to b, or use the "
            "quadratic formula."
        ),
        prompt_context=prompt_context,
    )


def _quadratic_conceptual_grounding() -> MathVerificationResult:
    return MathVerificationResult(
        status="conceptual",
        source="rulebook",
        response_text=(
            "For a quadratic, first put it in ax^2 + bx + c = 0 form. "
            "Try factorising by finding two numbers that multiply to ac and add "
            "to b. If it does not factorise neatly, use the quadratic formula."
        ),
        prompt_context=(
            "No exact quadratic expression was available. Use conceptual "
            "quadratic-solving guidance only."
        ),
    )


def _linear_conceptual_grounding() -> MathVerificationResult:
    return MathVerificationResult(
        status="conceptual",
        source="rulebook",
        response_text=(
            "For a linear equation, collect the x terms on one side and constants "
            "on the other side. Then divide both sides by the coefficient of x and "
            "substitute the answer back to check it."
        ),
        prompt_context=(
            "No exact linear expression was available. Use conceptual "
            "linear-equation guidance only."
        ),
    )


def _algebra_conceptual_grounding() -> MathVerificationResult:
    return MathVerificationResult(
        status="conceptual",
        source="rulebook",
        response_text=(
            "For algebra, first identify the unknown, then collect like terms. "
            "Use inverse operations to isolate the unknown, and check your final "
            "value by putting it back into the original expression or equation."
        ),
        prompt_context="Use deterministic algebra guidance; no exact expression was verified.",
    )


def _general_math_grounding() -> MathVerificationResult:
    return MathVerificationResult(
        status="conceptual",
        source="rulebook",
        response_text=(
            "Let's make the maths concrete. Write the exact equation, diagram "
            "values, or answer options first. Then identify what is being asked, "
            "choose the rule that connects the values, substitute carefully, "
            "simplify, and check the result against the question."
        ),
        prompt_context="Use broad deterministic mathematics guidance for a RAG/model miss.",
    )


def _looks_quadratic(normalized: str) -> bool:
    return "x**2" in normalized or bool(re.search(r"\bx\^2\b", normalized))


def _looks_linear_equation(normalized: str) -> bool:
    if "x" not in normalized or _looks_quadratic(normalized):
        return False
    return "=" in normalized or normalized.startswith("solve ")


def _extract_expression(normalized: str) -> str | None:
    selected = normalized
    for prefix in ("solve", "factorise", "factorize", "factor"):
        if selected.startswith(prefix + " "):
            selected = selected[len(prefix) + 1 :]
            break

    if "=" in selected:
        left, right = selected.split("=", 1)
        left = _sanitize_expression_side(left)
        right = _sanitize_expression_side(right)
        if not left or not right:
            return None
        selected = f"({left})-({right})"
    else:
        selected = _sanitize_expression_side(selected)

    return selected or None


def _sanitize_expression_side(text: str) -> str:
    selected = re.sub(r"[^x0-9+\-*/(). ]+", " ", text)
    selected = " ".join(selected.split())
    selected = re.sub(r"^x (?=\d|\()", "", selected)
    return selected
