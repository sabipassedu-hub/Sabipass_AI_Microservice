"""Layer 4 math input normalization.

Purpose: deterministically normalize calculator-tokenized math input into
safe symbolic forms. Constraints: no LLM parsing, no raw eval, sub-millisecond
target for simple transformations, and explicit ambiguity reporting.
"""

from __future__ import annotations

import re


_WORD_REPLACEMENTS = (
    (r"\bx\s+squared\b", "x**2"),
    (r"\bx\s+square\b", "x**2"),
    (r"\bsquared\b", "**2"),
    (r"\bsquare root of\b", "sqrt"),
    (r"\bsquare root\b", "sqrt"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\btimes\b", "*"),
    (r"\bmultiplied by\b", "*"),
    (r"\bdivide by\b", "/"),
    (r"\bdivided by\b", "/"),
    (r"\bequals\b", "="),
    (r"\bequal to\b", "="),
)


def normalize_math_input(raw_input: str) -> str:
    """Normalize common calculator/plain-English math into SymPy-friendly text."""
    normalized = raw_input.lower().replace("^", "**")
    for pattern, replacement in _WORD_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    normalized = re.sub(r"(?<=\d)(?=[a-z(])", "*", normalized)
    normalized = re.sub(r"(?<=[a-z)])(?=\d)", "*", normalized)
    normalized = re.sub(r"[^a-z0-9_+\-*/=(). ]+", " ", normalized)
    return " ".join(normalized.split())
