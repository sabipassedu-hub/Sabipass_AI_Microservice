"""Layer 11 ACTIVE_REGISTRY_POINTER management.

Purpose: provide immutable snapshot isolation for concept registry reads during
the full request lifecycle. Constraints: pointer swaps are process-local only,
requests must never read mutable globals directly, and Kubernetes consistency
requires shared external storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPOSITORY_ROOT / "data" / "processed" / "concept_registry.json"


def get_registry_snapshot() -> dict:
    """Return the active immutable registry snapshot."""
    return cast(dict, ACTIVE_REGISTRY_POINTER)


def _load_default_registry_snapshot() -> MappingProxyType:
    payload = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    return cast(MappingProxyType, _freeze(payload))


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


ACTIVE_REGISTRY_POINTER = _load_default_registry_snapshot()
