"""Mock JSON loader for the MVP ingestion pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pipelines.ingestion.documents import (
    AcademicStage,
    AnswerOption,
    Difficulty,
    ExamType,
    ParsedExamDocument,
    ParsedQuestion,
    SourceDocument,
    SourceType,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOCK_RAW_DIR = REPOSITORY_ROOT / "data" / "raw" / "mock"


class MockLoaderError(RuntimeError):
    """Raised when mock parser JSON cannot be loaded into the parser contract."""


def load_mock_documents(raw_dir: str | Path = DEFAULT_MOCK_RAW_DIR) -> tuple[ParsedExamDocument, ...]:
    """Load mock parser outputs shaped like future real PDF parser outputs."""
    selected_dir = Path(raw_dir)
    if not selected_dir.exists():
        raise MockLoaderError(f"Mock raw directory does not exist: {selected_dir}")
    if not selected_dir.is_dir():
        raise MockLoaderError(f"Mock raw path is not a directory: {selected_dir}")

    json_paths = tuple(sorted(selected_dir.glob("*.json")))
    if not json_paths:
        raise MockLoaderError(f"Mock raw directory contains no JSON files: {selected_dir}")

    return tuple(_load_mock_document(path) for path in json_paths)


def _load_mock_document(path: Path) -> ParsedExamDocument:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MockLoaderError(f"Could not read mock parser file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MockLoaderError(f"Invalid JSON in mock parser file: {path}") from exc

    try:
        return _parse_document_payload(payload)
    except (KeyError, TypeError) as exc:
        raise MockLoaderError(f"Mock parser file has invalid shape: {path}") from exc


def _parse_document_payload(payload: Any) -> ParsedExamDocument:
    if not isinstance(payload, dict):
        raise TypeError("mock parser payload must be an object")

    source = payload["source_document"]
    questions = payload["questions"]
    if not isinstance(source, dict) or not isinstance(questions, list):
        raise TypeError("mock parser source_document and questions have invalid types")

    return ParsedExamDocument(
        parser_version=str(payload["parser_version"]),
        source_document=_parse_source_document(source),
        questions=tuple(_parse_question(question) for question in questions),
    )


def _parse_source_document(source: dict[str, Any]) -> SourceDocument:
    return SourceDocument(
        doc_id=str(source["doc_id"]),
        source_type=cast(SourceType, source["source_type"]),
        subject=str(source["subject"]),
        exam_type=cast(ExamType, source["exam_type"]),
        academic_stage=cast(AcademicStage, source["academic_stage"]),
        year=int(source["year"]),
    )


def _parse_question(question: Any) -> ParsedQuestion:
    if not isinstance(question, dict):
        raise TypeError("question must be an object")

    answer_options = question["answer_options"]
    if not isinstance(answer_options, dict):
        raise TypeError("answer_options must be an object")

    return ParsedQuestion(
        question_id=str(question["question_id"]),
        page_number=int(question["page_number"]),
        topic=str(question["topic"]),
        difficulty=cast(Difficulty, question["difficulty"]),
        question_text=str(question["question_text"]),
        answer_options={
            cast(AnswerOption, key): str(value) for key, value in answer_options.items()
        },
        correct_answer=cast(AnswerOption, question["correct_answer"]),
        has_worked_solution=bool(question["has_worked_solution"]),
        worked_solution=str(question["worked_solution"]),
    )
