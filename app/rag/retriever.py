from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from chromadb.api.models.Collection import Collection


SOURCE_TAG_VERSION = "src:v1"
SOURCE_TAG_FIELDS = (
    "collection",
    "source_type",
    "doc_id",
    "chunk_id",
    "subject",
    "topic",
    "exam_type",
    "academic_stage",
    "year",
    "has_worked_solution",
    "rank",
)
_UNSAFE_TAG_CHARACTERS = re.compile(r"[^a-z0-9_.-]+")


class RetrievalError(RuntimeError):
    """Raised when ChromaDB retrieval fails for reasons other than no matches."""


@dataclass(frozen=True)
class RetrievalHit:
    collection_name: str
    document_id: str
    text: str
    metadata: dict[str, Any]
    distance: float
    confidence: float
    source_tag: str


def retrieve_from_collection(
    collection: Collection,
    query_embedding: Sequence[float],
    *,
    metadata_filter: Mapping[str, Any] | None = None,
    top_k: int = 3,
) -> list[RetrievalHit]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")
    if not query_embedding:
        raise ValueError("query_embedding must contain at least one value")

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [list(query_embedding)],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if metadata_filter:
        query_kwargs["where"] = _build_chroma_where_filter(metadata_filter)

    try:
        raw_results = collection.query(**query_kwargs)
    except Exception as exc:  # pragma: no cover - exact Chroma exceptions vary by version.
        raise RetrievalError(f"Failed to retrieve from collection '{collection.name}'") from exc

    return _parse_query_results(collection.name, raw_results)


def build_source_tag(
    *,
    collection_name: str,
    document_id: str,
    metadata: Mapping[str, Any],
    rank: int,
) -> str:
    tag_values = {
        "collection": collection_name,
        "source_type": metadata.get("source_type"),
        "doc_id": metadata.get("doc_id", document_id),
        "chunk_id": metadata.get("chunk_id"),
        "subject": metadata.get("subject"),
        "topic": metadata.get("topic"),
        "exam_type": metadata.get("exam_type"),
        "academic_stage": metadata.get("academic_stage"),
        "year": metadata.get("year"),
        "has_worked_solution": metadata.get("has_worked_solution"),
        "rank": rank,
    }
    fields = [SOURCE_TAG_VERSION]
    fields.extend(f"{key}={_sanitize_tag_value(tag_values[key])}" for key in SOURCE_TAG_FIELDS)
    return ";".join(fields)


def _parse_query_results(collection_name: str, raw_results: Mapping[str, Any]) -> list[RetrievalHit]:
    ids = _first_result_batch(raw_results.get("ids"))
    documents = _first_result_batch(raw_results.get("documents"))
    metadatas = _first_result_batch(raw_results.get("metadatas"))
    distances = _first_result_batch(raw_results.get("distances"))

    hits: list[RetrievalHit] = []
    for index, document_id in enumerate(ids):
        metadata = dict(metadatas[index] or {}) if index < len(metadatas) else {}
        distance = float(distances[index]) if index < len(distances) else 1.0
        text = str(documents[index]) if index < len(documents) and documents[index] else ""
        rank = index + 1

        hits.append(
            RetrievalHit(
                collection_name=collection_name,
                document_id=str(document_id),
                text=text,
                metadata=metadata,
                distance=distance,
                confidence=_confidence_from_cosine_distance(distance),
                source_tag=build_source_tag(
                    collection_name=collection_name,
                    document_id=str(document_id),
                    metadata=metadata,
                    rank=rank,
                ),
            )
        )

    return hits


def _first_result_batch(value: Any) -> list[Any]:
    if not value:
        return []
    first_batch = value[0]
    return list(first_batch or [])


def _build_chroma_where_filter(metadata_filter: Mapping[str, Any]) -> dict[str, Any]:
    filter_items = [(key, value) for key, value in metadata_filter.items()]
    if len(filter_items) == 1:
        key, value = filter_items[0]
        return {key: value}

    return {"$and": [{key: value} for key, value in filter_items]}


def _confidence_from_cosine_distance(distance: float) -> float:
    return max(0.0, min(1.0, 1.0 - distance))


def _sanitize_tag_value(value: Any) -> str:
    if value is None or value == "":
        return "none"
    if isinstance(value, bool):
        return str(value).lower()

    normalized = str(value).strip().lower().replace(" ", "_")
    normalized = _UNSAFE_TAG_CHARACTERS.sub("_", normalized)
    normalized = normalized.strip("_")
    return normalized or "none"
