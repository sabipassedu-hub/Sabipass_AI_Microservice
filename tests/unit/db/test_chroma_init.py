from pathlib import Path

import chromadb

from app.db.chroma import (
    ANALOGY_SANDBOX,
    COLLECTION_NAMES,
    CURRICULUM_VAULT,
    EXAM_BANK,
    HNSW_METADATA,
    get_analogy_sandbox,
    get_chroma_client,
    get_curriculum_vault,
    get_exam_bank,
    initialize_chroma,
)


def test_initialization_creates_all_required_collections(tmp_path: Path):
    collections = initialize_chroma(tmp_path)

    assert set(collections) == set(COLLECTION_NAMES)
    assert collections[EXAM_BANK].name == EXAM_BANK
    assert collections[CURRICULUM_VAULT].name == CURRICULUM_VAULT
    assert collections[ANALOGY_SANDBOX].name == ANALOGY_SANDBOX


def test_collections_are_independent_vector_spaces(tmp_path: Path):
    collections = initialize_chroma(tmp_path)
    collection_ids = {collection.id for collection in collections.values()}

    assert len(collection_ids) == 3


def test_all_collections_use_cosine_hnsw_space(tmp_path: Path):
    collections = initialize_chroma(tmp_path)

    for collection in collections.values():
        assert collection.metadata is not None
        assert collection.metadata["hnsw:space"] == "cosine"


def test_initialization_is_idempotent(tmp_path: Path):
    initialize_chroma(tmp_path)
    initialize_chroma(tmp_path)

    client = get_chroma_client(tmp_path)
    collection_names = {collection.name for collection in client.list_collections()}

    assert collection_names == set(COLLECTION_NAMES)
    assert len(collection_names) == 3


def test_collections_persist_across_new_client_instances(tmp_path: Path):
    initialize_chroma(tmp_path)

    fresh_client = chromadb.PersistentClient(path=str(tmp_path.resolve()))
    collection_names = {collection.name for collection in fresh_client.list_collections()}

    assert set(COLLECTION_NAMES).issubset(collection_names)


def test_collection_contents_are_isolated(tmp_path: Path):
    collections = initialize_chroma(tmp_path)
    exam_bank = collections[EXAM_BANK]

    exam_bank.add(
        ids=["waec-math-linear-equation-001"],
        documents=["Solve 2x + 4 = 10"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"topic": "linear_equations", "exam_type": "WAEC"}],
    )

    assert collections[EXAM_BANK].count() == 1
    assert collections[CURRICULUM_VAULT].count() == 0
    assert collections[ANALOGY_SANDBOX].count() == 0


def test_collection_getters_return_initialized_collections(tmp_path: Path):
    assert get_exam_bank(tmp_path).name == EXAM_BANK
    assert get_curriculum_vault(tmp_path).name == CURRICULUM_VAULT
    assert get_analogy_sandbox(tmp_path).name == ANALOGY_SANDBOX


def test_hnsw_metadata_contract_is_complete():
    assert HNSW_METADATA == {
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,
        "hnsw:M": 16,
        "hnsw:search_ef": 100,
    }
