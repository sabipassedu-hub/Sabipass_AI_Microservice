import json
from pathlib import Path

import pytest

from pipelines.ingestion.documents import ParsedExamDocument, ParsedQuestion, SourceDocument
from pipelines.ingestion.mock_loader import MockLoaderError, load_mock_documents
from pipelines.ingestion.pipeline import run_ingestion_pipeline


REPO_ROOT = Path(__file__).resolve().parents[3]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"


def test_mock_loader_reads_raw_mock_json_as_parsed_documents():
    documents = load_mock_documents(MOCK_RAW_DIR)

    assert len(documents) == 1
    document = documents[0]
    assert isinstance(document, ParsedExamDocument)
    assert document.parser_version == "mock_pdf_parser_v1"
    assert document.source_document.doc_id == "waec_math_mock_2024_001"
    assert document.source_document.source_type == "mock_pdf_parse"
    assert [question.question_id for question in document.questions] == [
        "waec_math_mock_2024_001_q01",
        "waec_math_mock_2024_001_q02",
        "waec_math_mock_2024_001_q03",
        "waec_math_mock_2024_001_q04",
        "waec_math_mock_2024_001_q05",
    ]


def test_mock_loader_rejects_missing_mock_directory(tmp_path: Path):
    missing_dir = tmp_path / "missing"

    with pytest.raises(MockLoaderError, match="does not exist"):
        load_mock_documents(missing_dir)


def test_ingestion_pipeline_can_replace_only_loader_boundary():
    source_document = SourceDocument(
        doc_id="real_pdf_math_2026_001",
        source_type="pdf_parse",
        subject="mathematics",
        exam_type="JAMB",
        academic_stage="senior_secondary",
        year=2026,
    )
    parsed_question = ParsedQuestion(
        question_id="real_pdf_math_2026_001_q01",
        page_number=4,
        topic="quadratic_equations",
        difficulty="medium",
        question_text="Solve x^2 - 5x + 6 = 0.",
        answer_options={"A": "1, 6", "B": "2, 3", "C": "3, 4", "D": "5, 6"},
        correct_answer="B",
        has_worked_solution=True,
        worked_solution="Factorise to get (x - 2)(x - 3) = 0, so x = 2 or x = 3.",
    )

    def fake_pdf_loader(raw_dir: Path) -> tuple[ParsedExamDocument, ...]:
        assert raw_dir == Path("source_files")
        return (
            ParsedExamDocument(
                parser_version="pdf_parser_v1",
                source_document=source_document,
                questions=(parsed_question,),
            ),
        )

    records = run_ingestion_pipeline(Path("source_files"), load_documents=fake_pdf_loader)

    assert len(records) == 1
    assert records[0].record_id == "real_pdf_math_2026_001_q01"
    assert records[0].source_document_id == "real_pdf_math_2026_001"
    assert records[0].metadata == {
        "subject": "mathematics",
        "topic": "quadratic_equations",
        "difficulty": "medium",
        "exam_type": "JAMB",
        "academic_stage": "senior_secondary",
        "has_worked_solution": True,
        "year": 2026,
    }
    assert "Solve x^2 - 5x + 6 = 0." in records[0].text


def test_default_ingestion_pipeline_uses_mock_loader():
    records = run_ingestion_pipeline(MOCK_RAW_DIR)

    assert [record.record_id for record in records] == [
        "waec_math_mock_2024_001_q01",
        "waec_math_mock_2024_001_q02",
        "waec_math_mock_2024_001_q03",
        "waec_math_mock_2024_001_q04",
        "waec_math_mock_2024_001_q05",
    ]
    assert all(record.metadata["subject"] == "mathematics" for record in records)


def test_mock_loader_reads_files_in_stable_order(tmp_path: Path):
    first_payload = _mock_payload("a_doc", "a_question")
    second_payload = _mock_payload("b_doc", "b_question")
    (tmp_path / "b.json").write_text(json.dumps(second_payload), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(first_payload), encoding="utf-8")

    documents = load_mock_documents(tmp_path)

    assert [document.source_document.doc_id for document in documents] == ["a_doc", "b_doc"]


def _mock_payload(doc_id: str, question_id: str) -> dict:
    return {
        "parser_version": "mock_pdf_parser_v1",
        "source_document": {
            "doc_id": doc_id,
            "source_type": "mock_pdf_parse",
            "subject": "mathematics",
            "exam_type": "WAEC",
            "academic_stage": "senior_secondary",
            "year": 2024,
        },
        "questions": [
            {
                "question_id": question_id,
                "page_number": 1,
                "topic": "linear_equations",
                "difficulty": "easy",
                "question_text": "If 3x + 4 = 19, find x.",
                "answer_options": {"A": "3", "B": "4", "C": "5", "D": "6"},
                "correct_answer": "C",
                "has_worked_solution": True,
                "worked_solution": "Subtract 4, then divide by 3.",
            }
        ],
    }
