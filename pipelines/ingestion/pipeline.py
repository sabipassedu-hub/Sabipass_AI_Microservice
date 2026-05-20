"""Loader-swappable ingestion pipeline for parsed exam documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from pipelines.ingestion.documents import ParsedExamDocument
from pipelines.ingestion.metadata_validator import validate_processed_question_records
from pipelines.ingestion.mock_loader import DEFAULT_MOCK_RAW_DIR, load_mock_documents


ParsedDocumentLoader = Callable[[Path], Iterable[ParsedExamDocument]]


@dataclass(frozen=True)
class IngestionRecord:
    record_id: str
    source_document_id: str
    source_type: str
    page_number: int
    text: str
    answer_options: dict[str, str]
    correct_answer: str
    worked_solution: str
    metadata: dict[str, str | int | bool]


def run_ingestion_pipeline(
    raw_dir: str | Path = DEFAULT_MOCK_RAW_DIR,
    *,
    load_documents: ParsedDocumentLoader = load_mock_documents,
    validate_metadata: bool = True,
) -> tuple[IngestionRecord, ...]:
    """Load parsed documents and convert them into downstream ingestion records."""
    selected_dir = Path(raw_dir)
    documents = tuple(load_documents(selected_dir))

    records = tuple(
        record
        for document in documents
        for record in _records_from_document(document)
    )
    if not validate_metadata:
        return records

    return validate_processed_question_records(records)


def _records_from_document(document: ParsedExamDocument) -> tuple[IngestionRecord, ...]:
    source = document.source_document
    return tuple(
        IngestionRecord(
            record_id=question.question_id,
            source_document_id=source.doc_id,
            source_type=source.source_type,
            page_number=question.page_number,
            text=question.question_text,
            answer_options={key: value for key, value in question.answer_options.items()},
            correct_answer=question.correct_answer,
            worked_solution=question.worked_solution,
            metadata={
                "subject": source.subject,
                "topic": question.topic,
                "difficulty": question.difficulty,
                "exam_type": source.exam_type,
                "academic_stage": source.academic_stage,
                "has_worked_solution": question.has_worked_solution,
                "year": source.year,
            },
        )
        for question in document.questions
    )
