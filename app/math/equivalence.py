"""Layer 4 expression equivalence checks.

Purpose: verify symbolic equality and supported transformation validity for
math-bearing responses. Constraints: no LLM derivation, no unchecked final
answers, and unsupported scopes must be reported honestly.
"""

from __future__ import annotations

from math_verify import verify
from sympy import simplify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations


_TRANSFORMATIONS = standard_transformations


def check_expression_equivalence(left: str, right: str) -> bool:
    """Check whether two supported mathematical expressions are equivalent."""
    left_expr = parse_expr(left, transformations=_TRANSFORMATIONS, evaluate=False)
    right_expr = parse_expr(right, transformations=_TRANSFORMATIONS, evaluate=False)
    return bool(verify(left_expr, right_expr, raise_on_error=False)) or simplify(
        left_expr - right_expr
    ) == 0
