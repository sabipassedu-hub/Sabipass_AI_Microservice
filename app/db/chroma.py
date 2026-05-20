from __future__ import annotations

from pathlib import Path
from typing import Final

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection


EXAM_BANK: Final[str] = "exam_bank"
CURRICULUM_VAULT: Final[str] = "curriculum_vault"
ANALOGY_SANDBOX: Final[str] = "analogy_sandbox"
COLLECTION_NAMES: Final[tuple[str, str, str]] = (
    EXAM_BANK,
    CURRICULUM_VAULT,
    ANALOGY_SANDBOX,
)

HNSW_METADATA: Final[dict[str, str | int]] = {
    "hnsw:space": "cosine",
    "hnsw:construction_ef": 200,
    "hnsw:M": 16,
    "hnsw:search_ef": 100,
}

REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DEFAULT_CHROMA_PATH: Final[Path] = REPOSITORY_ROOT / "data" / "embeddings"

_CLIENTS_BY_PATH: dict[Path, ClientAPI] = {}


def _resolve_storage_path(storage_path: str | Path | None = None) -> Path:
    selected_path = Path(storage_path) if storage_path is not None else DEFAULT_CHROMA_PATH
    return selected_path.resolve()


def get_chroma_client(storage_path: str | Path | None = None) -> ClientAPI:
    resolved_path = _resolve_storage_path(storage_path)
    resolved_path.mkdir(parents=True, exist_ok=True)

    if resolved_path not in _CLIENTS_BY_PATH:
        _CLIENTS_BY_PATH[resolved_path] = chromadb.PersistentClient(path=str(resolved_path))

    return _CLIENTS_BY_PATH[resolved_path]


def initialize_chroma(storage_path: str | Path | None = None) -> dict[str, Collection]:
    client = get_chroma_client(storage_path)

    exam_bank = client.get_or_create_collection(
        name=EXAM_BANK,
        metadata=HNSW_METADATA,
    )
    curriculum_vault = client.get_or_create_collection(
        name=CURRICULUM_VAULT,
        metadata=HNSW_METADATA,
    )
    analogy_sandbox = client.get_or_create_collection(
        name=ANALOGY_SANDBOX,
        metadata=HNSW_METADATA,
    )

    return {
        EXAM_BANK: exam_bank,
        CURRICULUM_VAULT: curriculum_vault,
        ANALOGY_SANDBOX: analogy_sandbox,
    }


def get_exam_bank(storage_path: str | Path | None = None) -> Collection:
    return initialize_chroma(storage_path)[EXAM_BANK]


def get_curriculum_vault(storage_path: str | Path | None = None) -> Collection:
    return initialize_chroma(storage_path)[CURRICULUM_VAULT]


def get_analogy_sandbox(storage_path: str | Path | None = None) -> Collection:
    return initialize_chroma(storage_path)[ANALOGY_SANDBOX]
