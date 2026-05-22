"""Embedding functions for retrieval.

Runtime retrieval uses FastEmbed-backed local embeddings. Unit tests can still
inject `deterministic_text_embedding` when they need tiny fixed vectors.
"""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from fastembed import TextEmbedding

from app.core.config import get_settings


DEFAULT_EMBEDDING_DIMENSIONS = 16
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def deterministic_text_embedding(
    text: str,
    *,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
) -> list[float]:
    """Create a stable embedding for mock/demo retrieval without network calls."""
    if dimensions <= 0:
        raise ValueError("dimensions must be greater than 0")

    buckets = [0.0] * dimensions
    tokens = TOKEN_PATTERN.findall(text.lower())
    if not tokens:
        buckets[0] = 1.0
        return buckets

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket_index = int.from_bytes(digest[:4], "big") % dimensions
        buckets[bucket_index] += 1.0

    magnitude = math.sqrt(sum(value * value for value in buckets))
    return [value / magnitude for value in buckets]


def embed_query_text(text: str) -> list[float]:
    """Embed one text query with the configured local FastEmbed model."""
    embeddings = list(_get_text_embedding().embed([text]))
    if not embeddings:
        raise RuntimeError("FastEmbed did not return an embedding")

    return [float(value) for value in embeddings[0]]


def warm_embedding_model() -> str:
    """Load the configured FastEmbed model before demo traffic arrives."""
    model_name = get_settings().embedding_model_name
    list(_get_text_embedding().embed(["sabi pass embedding warmup"]))
    return model_name


@lru_cache(maxsize=1)
def _get_text_embedding() -> TextEmbedding:
    return TextEmbedding(model_name=get_settings().embedding_model_name)
