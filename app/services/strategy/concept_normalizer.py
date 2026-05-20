"""Layer 2 concept normalization.

Purpose: map student language to canonical curriculum keys using the registry
snapshot and approved aliases. Constraints: prefer dictionary and cached local
semantic paths, degrade quickly on misses, and keep LLM fallback outside the
Phase 3 request critical path.
"""

import re
from dataclasses import dataclass
from typing import Literal


NormalizationStatus = Literal["strict", "semantic", "degraded", "needs_clarification"]

GENERAL_MATH_SIGNALS = {
    "answer",
    "calculate",
    "class",
    "equation",
    "exam",
    "find",
    "jamb",
    "math",
    "mathematics",
    "question",
    "solve",
    "waec",
    "x",
}


@dataclass(frozen=True)
class NormalizationResult:
    """Canonical concept resolution for strategy compilation."""

    concept_key: str | None
    confidence: float
    status: NormalizationStatus
    matched_text: str | None = None


def normalize_concept(raw_input: str, *, registry_snapshot: dict) -> NormalizationResult:
    """Normalize a topic phrase to a canonical concept key."""
    text = _normalize_text(raw_input)
    canonical_keys = registry_snapshot["canonical_keys"]

    if not text:
        return _needs_clarification()

    if text in canonical_keys:
        return NormalizationResult(
            concept_key=text,
            confidence=1.0,
            status="strict",
            matched_text=text,
        )

    semantic_result = _match_local_semantic(text, canonical_keys)
    if semantic_result is not None:
        return semantic_result

    alias_result = _match_alias(text, registry_snapshot["aliases"])
    if alias_result is not None:
        return alias_result

    if _has_general_math_signal(text):
        return NormalizationResult(
            concept_key="general_mathematics",
            confidence=0.4,
            status="degraded",
        )

    return _needs_clarification()


def _normalize_text(raw_input: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_+\-*/= ]+", " ", raw_input.lower())
    return " ".join(cleaned.split())


def _match_alias(text: str, aliases: dict[str, str]) -> NormalizationResult | None:
    for alias, concept_key in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if _contains_phrase(text, alias):
            return NormalizationResult(
                concept_key=concept_key,
                confidence=0.95,
                status="strict",
                matched_text=alias,
            )
    return None


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _match_local_semantic(text: str, canonical_keys: dict[str, dict]) -> NormalizationResult | None:
    input_tokens = _tokens(text)
    best_key: str | None = None
    best_score = 0.0

    for concept_key, topic in canonical_keys.items():
        if concept_key == "general_mathematics":
            continue
        candidate_tokens = _candidate_tokens(concept_key, topic)
        if not candidate_tokens:
            continue

        overlap = input_tokens & candidate_tokens
        score = len(overlap) / len(candidate_tokens)
        if score > best_score:
            best_score = score
            best_key = concept_key

    if best_key is not None and best_score >= 0.5:
        return NormalizationResult(
            concept_key=best_key,
            confidence=0.9,
            status="semantic",
        )

    return None


def _tokens(text: str) -> set[str]:
    tokens = set(text.replace("_", " ").split())
    if "trig" in tokens:
        tokens.add("trigonometric")
    if "ratios" in tokens:
        tokens.add("ratio")
    if "equations" in tokens:
        tokens.add("equation")
    return tokens


def _candidate_tokens(concept_key: str, topic: dict) -> set[str]:
    text = f"{concept_key} {topic['display_name']}"
    tokens = _tokens(_normalize_text(text))
    return {token for token in tokens if len(token) > 2}


def _has_general_math_signal(text: str) -> bool:
    return bool(_tokens(text) & GENERAL_MATH_SIGNALS)


def _needs_clarification() -> NormalizationResult:
    return NormalizationResult(
        concept_key=None,
        confidence=0.0,
        status="needs_clarification",
    )
