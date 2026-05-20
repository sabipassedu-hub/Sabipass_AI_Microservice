"""Typed parsed-document contracts for ingestion loaders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AnswerOption = Literal["A", "B", "C", "D"]
Difficulty = Literal["foundation", "easy", "medium", "hard"]
ExamType = Literal["WAEC", "JAMB"]
AcademicStage = Literal["junior_secondary", "senior_secondary"]
SourceType = Literal["mock_pdf_parse", "pdf_parse"]


@dataclass(frozen=True)
class SourceDocument:
    doc_id: str
    source_type: SourceType
    subject: str
    exam_type: ExamType
    academic_stage: AcademicStage
    year: int


@dataclass(frozen=True)
class ParsedQuestion:
    question_id: str
    page_number: int
    topic: str
    difficulty: Difficulty
    question_text: str
    answer_options: dict[AnswerOption, str]
    correct_answer: AnswerOption
    has_worked_solution: bool
    worked_solution: str


@dataclass(frozen=True)
class ParsedExamDocument:
    parser_version: str
    source_document: SourceDocument
    questions: tuple[ParsedQuestion, ...]
