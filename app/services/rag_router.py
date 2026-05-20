"""Layer 3 service-level RAG routing.

Purpose: execute the immutable RAG plan produced by Layer 2. Constraints:
precision mode selects a strategy-owned Chroma collection and embeds the
canonical concept key only; fallback mode reads bounded foundational summaries
without vector search.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from chromadb.api.models.Collection import Collection

from app.rag.retriever import RetrievalHit, retrieve_from_collection
from app.schemas.strategy import FilterValue, RagMode, StateStrategy


MAX_PRECISION_TOP_K = 5
MAX_FALLBACK_TOKENS = 600
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FALLBACK_DIR = REPOSITORY_ROOT / "data" / "processed" / "fallback"
EmbedQuery = Callable[[str], Sequence[float]]


class RagRouterError(RuntimeError):
    """Raised when the service-level RAG route cannot be executed safely."""


class PrecisionRetrievalError(RagRouterError):
    """Raised when precision retrieval is missing required execution inputs."""


class FallbackSummaryError(RagRouterError):
    """Raised when a fallback summary is missing or violates its contract."""


@dataclass(frozen=True)
class FallbackSummary:
    concept_key: str
    summary_text: str
    token_count: int
    version: str
    source_path: Path


@dataclass(frozen=True)
class RagContext:
    mode: RagMode
    query_concept_key: str | None
    context_text: str
    hits: tuple[RetrievalHit, ...]
    source_tags: tuple[str, ...]
    fallback_summary: FallbackSummary | None = None


@dataclass(frozen=True)
class RagQuery:
    target_collection: str
    query_concept_key: str
    metadata_filter: dict[str, FilterValue]
    top_k: int


def route_and_retrieve_context(payload: Any, **kwargs: Any) -> RagContext | str:
    """Route RAG context.

    Phase 7 will pass a compiled StateStrategy from the API layer. Until that
    wiring lands, the legacy request-path placeholder remains for existing
    integration tests that still call this function with a request object.
    """
    if isinstance(payload, StateStrategy):
        return retrieve_context_for_strategy(payload, **kwargs)

    return "Baseline curriculum placeholder context text."


def retrieve_context_for_strategy(
    strategy: StateStrategy,
    *,
    collections: Mapping[str, Collection] | None = None,
    embed_query: EmbedQuery | None = None,
    fallback_dir: str | Path | None = None,
) -> RagContext:
    """Execute the RAG portion of an immutable StateStrategy."""
    rag_strategy = strategy.rag_strategy

    if rag_strategy.mode == "none":
        return _empty_context(mode="none", query_concept_key=rag_strategy.query_concept_key)

    if rag_strategy.mode == "fallback":
        return _retrieve_fallback_context(rag_strategy.query_concept_key, fallback_dir)

    if rag_strategy.mode == "precision":
        return _retrieve_precision_context(
            strategy,
            collections=collections,
            embed_query=embed_query,
        )

    raise RagRouterError(f"Unsupported RAG mode: {rag_strategy.mode}")


def load_fallback_summary(
    concept_key: str,
    *,
    fallback_dir: str | Path | None = None,
) -> FallbackSummary:
    """Load a foundational fallback summary for a normalized concept key."""
    normalized_key = concept_key.strip()
    if not normalized_key:
        raise FallbackSummaryError("fallback concept_key must not be empty")

    selected_dir = Path(fallback_dir) if fallback_dir is not None else DEFAULT_FALLBACK_DIR
    return _load_fallback_summary_cached(str(selected_dir.resolve()), normalized_key)


def build_precision_rag_query(strategy: StateStrategy) -> RagQuery:
    """Construct a precision RAG query from Layer 2's normalized concept output."""
    rag_strategy = strategy.rag_strategy
    if rag_strategy.mode != "precision":
        raise PrecisionRetrievalError("precision query construction requires precision mode")
    if not rag_strategy.target_collection:
        raise PrecisionRetrievalError("precision mode requires target_collection")
    if not strategy.normalized_concept:
        raise PrecisionRetrievalError("precision mode requires normalized_concept")
    if rag_strategy.query_concept_key != strategy.normalized_concept:
        raise PrecisionRetrievalError(
            "precision query concept must match strategy.normalized_concept"
        )

    metadata_filter = rag_strategy.filter_dict
    if metadata_filter.get("topic") != strategy.normalized_concept:
        raise PrecisionRetrievalError(
            "precision topic filter must match strategy.normalized_concept"
        )

    top_k = min(rag_strategy.top_k, MAX_PRECISION_TOP_K)
    if top_k <= 0:
        raise PrecisionRetrievalError("precision mode requires top_k greater than 0")

    return RagQuery(
        target_collection=rag_strategy.target_collection,
        query_concept_key=strategy.normalized_concept,
        metadata_filter=metadata_filter,
        top_k=top_k,
    )


def _retrieve_precision_context(
    strategy: StateStrategy,
    *,
    collections: Mapping[str, Collection] | None,
    embed_query: EmbedQuery | None,
) -> RagContext:
    if embed_query is None:
        raise PrecisionRetrievalError("precision mode requires an embed_query callable")

    rag_query = build_precision_rag_query(strategy)
    selected_collections = _resolve_collections(collections)
    try:
        collection = selected_collections[rag_query.target_collection]
    except KeyError as exc:
        raise PrecisionRetrievalError(
            f"Collection '{rag_query.target_collection}' is not available"
        ) from exc

    query_embedding = embed_query(rag_query.query_concept_key)
    hits = tuple(
        retrieve_from_collection(
            collection,
            query_embedding,
            metadata_filter=rag_query.metadata_filter,
            top_k=rag_query.top_k,
        )
    )

    return RagContext(
        mode="precision",
        query_concept_key=rag_query.query_concept_key,
        context_text=_format_precision_context(hits),
        hits=hits,
        source_tags=tuple(hit.source_tag for hit in hits),
    )


def _retrieve_fallback_context(
    query_concept_key: str | None,
    fallback_dir: str | Path | None,
) -> RagContext:
    if not query_concept_key:
        raise FallbackSummaryError("fallback mode requires query_concept_key")

    summary = load_fallback_summary(query_concept_key, fallback_dir=fallback_dir)
    return RagContext(
        mode="fallback",
        query_concept_key=query_concept_key,
        context_text=summary.summary_text,
        hits=(),
        source_tags=(),
        fallback_summary=summary,
    )


def _resolve_collections(
    collections: Mapping[str, Collection] | None,
) -> Mapping[str, Collection]:
    if collections is not None:
        return collections

    from app.db.chroma import initialize_chroma

    return initialize_chroma()


def _empty_context(*, mode: RagMode, query_concept_key: str | None) -> RagContext:
    return RagContext(
        mode=mode,
        query_concept_key=query_concept_key,
        context_text="",
        hits=(),
        source_tags=(),
    )


def _format_precision_context(hits: Sequence[RetrievalHit]) -> str:
    return "\n\n".join(
        f"{hit.source_tag}\n{hit.text.strip()}" for hit in hits if hit.text.strip()
    )


@lru_cache(maxsize=64)
def _load_fallback_summary_cached(fallback_dir: str, concept_key: str) -> FallbackSummary:
    selected_path = _find_fallback_summary_path(Path(fallback_dir), concept_key)

    try:
        raw_summary = json.loads(selected_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FallbackSummaryError(f"Could not read fallback summary: {selected_path}") from exc
    except json.JSONDecodeError as exc:
        raise FallbackSummaryError(f"Invalid fallback summary JSON: {selected_path}") from exc

    return _parse_fallback_summary(raw_summary, selected_path)


def _find_fallback_summary_path(fallback_dir: Path, concept_key: str) -> Path:
    for candidate in _fallback_summary_candidates(fallback_dir, concept_key):
        if candidate.exists():
            return candidate

    raise FallbackSummaryError(f"No fallback summary found for concept '{concept_key}'")


def _fallback_summary_candidates(fallback_dir: Path, concept_key: str) -> tuple[Path, ...]:
    return (
        fallback_dir / f"{concept_key}_summary.json",
        fallback_dir / f"{concept_key}_v1_summary.json",
    )


def _parse_fallback_summary(raw_summary: Any, source_path: Path) -> FallbackSummary:
    if not isinstance(raw_summary, dict):
        raise FallbackSummaryError("fallback summary must be a JSON object")

    required_fields = {"concept_key", "summary_text", "token_count", "version"}
    if set(raw_summary) != required_fields:
        raise FallbackSummaryError("fallback summary has an invalid shape")

    concept_key = raw_summary["concept_key"]
    summary_text = raw_summary["summary_text"]
    token_count = raw_summary["token_count"]
    version = raw_summary["version"]

    if not isinstance(concept_key, str) or not concept_key.strip():
        raise FallbackSummaryError("fallback summary concept_key must be a non-empty string")
    if not isinstance(summary_text, str) or not summary_text.strip():
        raise FallbackSummaryError("fallback summary_text must be a non-empty string")
    if not isinstance(token_count, int):
        raise FallbackSummaryError("fallback summary token_count must be an integer")
    if not isinstance(version, str) or not version.strip():
        raise FallbackSummaryError("fallback summary version must be a non-empty string")

    actual_token_count = len(summary_text.split())
    if token_count != actual_token_count:
        raise FallbackSummaryError("fallback summary token_count does not match summary_text")
    if actual_token_count > MAX_FALLBACK_TOKENS:
        raise FallbackSummaryError("fallback summary must stay at or below 600 tokens")

    return FallbackSummary(
        concept_key=concept_key,
        summary_text=summary_text,
        token_count=token_count,
        version=version,
        source_path=source_path,
    )
