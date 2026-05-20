"""Seed Chroma exam-bank data from validated ingestion records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from chromadb.api.models.Collection import Collection

from app.db.chroma import ANALOGY_SANDBOX, CURRICULUM_VAULT, EXAM_BANK, initialize_chroma
from app.rag.embeddings import embed_query_text
from pipelines.ingestion.metadata_validator import validate_processed_question_records
from pipelines.ingestion.mock_loader import DEFAULT_MOCK_RAW_DIR
from pipelines.ingestion.pipeline import IngestionRecord, ParsedDocumentLoader, run_ingestion_pipeline


EmbeddingFunction = Callable[[str], Sequence[float]]


@dataclass(frozen=True)
class ChromaSeedResult:
    collection_name: str
    records_seeded: int
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class DemoSeedResult:
    exam_bank: ChromaSeedResult
    curriculum_vault: ChromaSeedResult
    analogy_sandbox: ChromaSeedResult


def seed_demo_collections(
    raw_dir: str | Path = DEFAULT_MOCK_RAW_DIR,
    *,
    storage_path: str | Path | None = None,
    load_documents: ParsedDocumentLoader | None = None,
    embed_text: EmbeddingFunction = embed_query_text,
) -> DemoSeedResult:
    """Seed all demo Chroma collections from the packaged mock data."""
    pipeline_kwargs = {}
    if load_documents is not None:
        pipeline_kwargs["load_documents"] = load_documents

    records = tuple(validate_processed_question_records(run_ingestion_pipeline(raw_dir, **pipeline_kwargs)))
    collections = initialize_chroma(storage_path)
    return DemoSeedResult(
        exam_bank=seed_exam_bank_from_records(
            records,
            collection=collections[EXAM_BANK],
            embed_text=embed_text,
        ),
        curriculum_vault=_seed_support_collection(
            records,
            collection=collections[CURRICULUM_VAULT],
            id_prefix="curriculum",
            source_type="mock_curriculum_summary",
            embed_text=embed_text,
        ),
        analogy_sandbox=_seed_support_collection(
            records,
            collection=collections[ANALOGY_SANDBOX],
            id_prefix="analogy",
            source_type="mock_analogy",
            embed_text=embed_text,
        ),
    )


def seed_mock_exam_bank(
    raw_dir: str | Path = DEFAULT_MOCK_RAW_DIR,
    *,
    storage_path: str | Path | None = None,
    load_documents: ParsedDocumentLoader | None = None,
    embed_text: EmbeddingFunction = embed_query_text,
) -> ChromaSeedResult:
    """Run the mock ingestion pipeline and seed validated records into exam_bank."""
    pipeline_kwargs = {}
    if load_documents is not None:
        pipeline_kwargs["load_documents"] = load_documents

    records = run_ingestion_pipeline(raw_dir, **pipeline_kwargs)
    return seed_exam_bank_from_records(
        records,
        storage_path=storage_path,
        embed_text=embed_text,
    )


def seed_exam_bank_from_records(
    records: Iterable[IngestionRecord],
    *,
    storage_path: str | Path | None = None,
    collection: Collection | None = None,
    embed_text: EmbeddingFunction = embed_query_text,
) -> ChromaSeedResult:
    """Upsert validated processed question records into the Chroma exam bank."""
    valid_records = validate_processed_question_records(records)
    selected_collection = collection or initialize_chroma(storage_path)[EXAM_BANK]

    if not valid_records:
        return ChromaSeedResult(
            collection_name=selected_collection.name,
            records_seeded=0,
            record_ids=(),
        )

    record_ids = tuple(record.record_id for record in valid_records)
    selected_collection.upsert(
        ids=list(record_ids),
        documents=[_format_record_document(record) for record in valid_records],
        embeddings=[
            list(embed_text(_format_record_embedding_text(record))) for record in valid_records
        ],
        metadatas=[_build_chroma_metadata(record) for record in valid_records],
    )

    return ChromaSeedResult(
        collection_name=selected_collection.name,
        records_seeded=len(record_ids),
        record_ids=record_ids,
    )


def _format_record_document(record: IngestionRecord) -> str:
    option_lines = [
        f"{option}. {record.answer_options[option]}"
        for option in ("A", "B", "C", "D")
        if option in record.answer_options
    ]
    parts = [
        f"Question: {record.text.strip()}",
        "Options:",
        *option_lines,
        f"Correct answer: {record.correct_answer}",
    ]
    if record.worked_solution.strip():
        parts.append(f"Worked solution: {record.worked_solution.strip()}")

    return "\n".join(parts)


def _format_record_embedding_text(record: IngestionRecord) -> str:
    return " ".join(
        [
            str(record.metadata["topic"]),
            record.text,
            record.worked_solution,
        ]
    )


def _build_chroma_metadata(record: IngestionRecord) -> dict[str, str | int | bool]:
    return {
        **record.metadata,
        "source_type": record.source_type,
        "doc_id": record.source_document_id,
        "chunk_id": record.record_id,
    }


def _seed_support_collection(
    records: tuple[IngestionRecord, ...],
    *,
    collection: Collection,
    id_prefix: str,
    source_type: str,
    embed_text: EmbeddingFunction,
) -> ChromaSeedResult:
    if not records:
        return ChromaSeedResult(
            collection_name=collection.name,
            records_seeded=0,
            record_ids=(),
        )

    record_ids = tuple(f"{id_prefix}_{record.record_id}" for record in records)
    collection.upsert(
        ids=list(record_ids),
        documents=[_format_record_document(record) for record in records],
        embeddings=[
            list(embed_text(_format_record_embedding_text(record))) for record in records
        ],
        metadatas=[
            {
                **_build_chroma_metadata(record),
                "source_type": source_type,
                "chunk_id": record_id,
            }
            for record, record_id in zip(records, record_ids)
        ],
    )
    return ChromaSeedResult(
        collection_name=collection.name,
        records_seeded=len(record_ids),
        record_ids=record_ids,
    )
