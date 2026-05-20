import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"


DOCUMENT_FIELDS = {
    "doc_id",
    "source_type",
    "subject",
    "exam_type",
    "academic_stage",
    "year",
}
QUESTION_FIELDS = {
    "question_id",
    "page_number",
    "topic",
    "difficulty",
    "question_text",
    "answer_options",
    "correct_answer",
    "has_worked_solution",
    "worked_solution",
}


def load_mock_files() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(MOCK_RAW_DIR.glob("*.json"))
    ]


def test_mock_parser_input_directory_contains_json_files():
    assert MOCK_RAW_DIR.is_dir()
    assert list(MOCK_RAW_DIR.glob("*.json"))


def test_mock_parser_inputs_have_real_pdf_parser_shape():
    for payload in load_mock_files():
        assert set(payload) == {"parser_version", "source_document", "questions"}
        assert isinstance(payload["parser_version"], str)
        assert set(payload["source_document"]) == DOCUMENT_FIELDS
        assert isinstance(payload["questions"], list)
        assert payload["questions"]


def test_mock_parser_question_metadata_matches_rag_requirements():
    for payload in load_mock_files():
        source_document = payload["source_document"]

        assert source_document["source_type"] == "mock_pdf_parse"
        assert source_document["subject"] == "mathematics"
        assert source_document["exam_type"] in {"WAEC", "JAMB"}
        assert isinstance(source_document["year"], int)

        for question in payload["questions"]:
            assert set(question) == QUESTION_FIELDS
            assert isinstance(question["page_number"], int)
            assert question["topic"]
            assert question["difficulty"] in {"foundation", "easy", "medium", "hard"}
            assert question["question_text"]
            assert set(question["answer_options"]) == {"A", "B", "C", "D"}
            assert question["correct_answer"] in {"A", "B", "C", "D"}
            assert isinstance(question["has_worked_solution"], bool)
            assert question["worked_solution"]
