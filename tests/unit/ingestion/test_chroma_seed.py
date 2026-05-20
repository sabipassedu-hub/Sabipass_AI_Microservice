from pathlib import Path

import pytest

from app.db.chroma import ANALOGY_SANDBOX, CURRICULUM_VAULT, EXAM_BANK, initialize_chroma
from app.rag.embeddings import deterministic_text_embedding
from pipelines.ingestion.chroma_seed import (
    seed_demo_collections,
    seed_exam_bank_from_records,
    seed_mock_exam_bank,
)
from pipelines.ingestion.metadata_validator import MetadataValidationError
from pipelines.ingestion.pipeline import IngestionRecord, run_ingestion_pipeline


REPO_ROOT = Path(__file__).resolve().parents[3]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"


def test_seed_mock_exam_bank_upserts_processed_records(tmp_path: Path):
    result = seed_mock_exam_bank(
        MOCK_RAW_DIR,
        storage_path=tmp_path,
        embed_text=deterministic_text_embedding,
    )
    collection = initialize_chroma(tmp_path)[EXAM_BANK]
    seeded = collection.get(
        ids=list(result.record_ids),
        include=["documents", "metadatas"],
    )

    assert result.collection_name == EXAM_BANK
    assert result.records_seeded == 5
    assert collection.count() == 5
    assert seeded["ids"] == [
        "waec_math_mock_2024_001_q01",
        "waec_math_mock_2024_001_q02",
        "waec_math_mock_2024_001_q03",
        "waec_math_mock_2024_001_q04",
        "waec_math_mock_2024_001_q05",
    ]
    assert "Question: If 3x + 4 = 19" in seeded["documents"][0]
    assert seeded["metadatas"][0] == {
        "subject": "mathematics",
        "topic": "linear_equations",
        "difficulty": "easy",
        "exam_type": "WAEC",
        "academic_stage": "senior_secondary",
        "has_worked_solution": True,
        "year": 2024,
        "source_type": "mock_pdf_parse",
        "doc_id": "waec_math_mock_2024_001",
        "chunk_id": "waec_math_mock_2024_001_q01",
    }


def test_seed_mock_exam_bank_is_idempotent(tmp_path: Path):
    seed_mock_exam_bank(
        MOCK_RAW_DIR,
        storage_path=tmp_path,
        embed_text=deterministic_text_embedding,
    )
    seed_mock_exam_bank(
        MOCK_RAW_DIR,
        storage_path=tmp_path,
        embed_text=deterministic_text_embedding,
    )

    collection = initialize_chroma(tmp_path)[EXAM_BANK]

    assert collection.count() == 5


def test_seed_demo_collections_populates_all_local_demo_collections(tmp_path: Path):
    result = seed_demo_collections(
        MOCK_RAW_DIR,
        storage_path=tmp_path,
        embed_text=deterministic_text_embedding,
    )
    collections = initialize_chroma(tmp_path)

    assert result.exam_bank.records_seeded == 5
    assert result.curriculum_vault.records_seeded == 5
    assert result.analogy_sandbox.records_seeded == 5
    assert collections[EXAM_BANK].count() == 5
    assert collections[CURRICULUM_VAULT].count() == 5
    assert collections[ANALOGY_SANDBOX].count() == 5


def test_seed_rejects_invalid_metadata_before_writing(tmp_path: Path):
    record = _record_with_metadata(topic="not_in_registry")

    with pytest.raises(MetadataValidationError, match="topic is not canonical"):
        seed_exam_bank_from_records((record,), storage_path=tmp_path)

    collection = initialize_chroma(tmp_path)[EXAM_BANK]
    assert collection.count() == 0


def test_seeded_records_can_be_retrieved_by_metadata_filter(tmp_path: Path):
    seed_mock_exam_bank(
        MOCK_RAW_DIR,
        storage_path=tmp_path,
        embed_text=deterministic_text_embedding,
    )
    collection = initialize_chroma(tmp_path)[EXAM_BANK]

    results = collection.query(
        query_embeddings=[deterministic_text_embedding("linear_equations")],
        n_results=2,
        include=["documents", "metadatas"],
        where={"topic": "linear_equations"},
    )

    assert results["ids"] == [["waec_math_mock_2024_001_q01"]]
    assert results["metadatas"][0][0]["chunk_id"] == "waec_math_mock_2024_001_q01"


def test_seed_exam_bank_from_records_accepts_injected_collection(tmp_path: Path):
    records = run_ingestion_pipeline(MOCK_RAW_DIR)
    collection = initialize_chroma(tmp_path)[EXAM_BANK]

    result = seed_exam_bank_from_records(
        records,
        collection=collection,
        embed_text=deterministic_text_embedding,
    )

    assert result.records_seeded == 5
    assert collection.count() == 5


def _record_with_metadata(**metadata_overrides) -> IngestionRecord:
    metadata = {
        "subject": "mathematics",
        "topic": "linear_equations",
        "difficulty": "easy",
        "exam_type": "WAEC",
        "academic_stage": "senior_secondary",
        "has_worked_solution": True,
        "year": 2024,
    }
    metadata.update(metadata_overrides)
    return IngestionRecord(
        record_id="question_001",
        source_document_id="document_001",
        source_type="mock_pdf_parse",
        page_number=1,
        text="If 3x + 4 = 19, find x.",
        answer_options={"A": "3", "B": "4", "C": "5", "D": "6"},
        correct_answer="C",
        worked_solution="Subtract 4, then divide by 3.",
        metadata=metadata,
    )
