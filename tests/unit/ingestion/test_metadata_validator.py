from pathlib import Path

import pytest

from pipelines.ingestion.metadata_validator import (
    MetadataValidationError,
    REQUIRED_METADATA_FIELDS,
    load_canonical_topic_keys,
    validate_processed_question_metadata,
    validate_processed_question_records,
)
from pipelines.ingestion.pipeline import IngestionRecord, run_ingestion_pipeline


REPO_ROOT = Path(__file__).resolve().parents[3]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def test_default_pipeline_validates_processed_question_metadata():
    records = run_ingestion_pipeline(MOCK_RAW_DIR)

    assert len(records) == 5
    assert all(set(record.metadata) == REQUIRED_METADATA_FIELDS for record in records)


def test_loads_canonical_topic_keys_from_registry():
    canonical_topics = load_canonical_topic_keys(REGISTRY_PATH)

    assert "linear_equations" in canonical_topics
    assert "trigonometric_ratios" in canonical_topics


def test_validator_rejects_unknown_topic():
    record = _record_with_metadata(topic="invented_topic")

    with pytest.raises(MetadataValidationError, match="topic is not canonical"):
        validate_processed_question_records((record,), canonical_topics={"linear_equations"})


def test_validator_rejects_missing_required_metadata_field():
    metadata = _valid_metadata()
    metadata.pop("year")

    with pytest.raises(MetadataValidationError, match="metadata fields"):
        validate_processed_question_metadata(
            metadata,
            canonical_topics={"linear_equations"},
            record_id="question_001",
        )


def test_validator_rejects_invalid_metadata_types():
    metadata = _valid_metadata(year=True)

    with pytest.raises(MetadataValidationError, match="year"):
        validate_processed_question_metadata(
            metadata,
            canonical_topics={"linear_equations"},
            record_id="question_001",
        )


def test_validator_rejects_duplicate_record_ids():
    record = _record_with_metadata(topic="linear_equations")

    with pytest.raises(MetadataValidationError, match="record_id must be unique"):
        validate_processed_question_records(
            (record, record),
            canonical_topics={"linear_equations"},
        )


def _record_with_metadata(**metadata_overrides) -> IngestionRecord:
    return IngestionRecord(
        record_id="question_001",
        source_document_id="document_001",
        source_type="mock_pdf_parse",
        page_number=1,
        text="If 3x + 4 = 19, find x.",
        answer_options={"A": "3", "B": "4", "C": "5", "D": "6"},
        correct_answer="C",
        worked_solution="Subtract 4, then divide by 3.",
        metadata=_valid_metadata(**metadata_overrides),
    )


def _valid_metadata(**overrides):
    metadata = {
        "subject": "mathematics",
        "topic": "linear_equations",
        "difficulty": "easy",
        "exam_type": "WAEC",
        "academic_stage": "senior_secondary",
        "has_worked_solution": True,
        "year": 2024,
    }
    metadata.update(overrides)
    return metadata
