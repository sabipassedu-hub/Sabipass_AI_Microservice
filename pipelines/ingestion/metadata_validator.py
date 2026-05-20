"""Validation for processed question metadata before retrieval indexing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONCEPT_REGISTRY_PATH = REPOSITORY_ROOT / "data" / "processed" / "concept_registry.json"

REQUIRED_METADATA_FIELDS = frozenset(
    {
        "subject",
        "topic",
        "difficulty",
        "exam_type",
        "academic_stage",
        "has_worked_solution",
        "year",
    }
)
ALLOWED_SUBJECTS = frozenset({"mathematics"})
ALLOWED_DIFFICULTIES = frozenset({"foundation", "easy", "medium", "hard"})
ALLOWED_EXAM_TYPES = frozenset({"WAEC", "JAMB"})
ALLOWED_ACADEMIC_STAGES = frozenset({"junior_secondary", "senior_secondary"})


class MetadataValidationError(ValueError):
    """Raised when processed question metadata cannot be safely indexed."""


def load_canonical_topic_keys(
    registry_path: str | Path = DEFAULT_CONCEPT_REGISTRY_PATH,
) -> frozenset[str]:
    """Load canonical concept keys that processed question topics must target."""
    selected_path = Path(registry_path)
    try:
        registry = json.loads(selected_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MetadataValidationError(f"Could not read concept registry: {selected_path}") from exc
    except json.JSONDecodeError as exc:
        raise MetadataValidationError(f"Invalid concept registry JSON: {selected_path}") from exc

    canonical_keys = registry.get("canonical_keys") if isinstance(registry, dict) else None
    if not isinstance(canonical_keys, dict) or not canonical_keys:
        raise MetadataValidationError("concept registry must contain canonical_keys")

    return frozenset(str(key) for key in canonical_keys)


def validate_processed_question_records(
    records: Iterable[Any],
    *,
    canonical_topics: Iterable[str] | None = None,
    registry_path: str | Path = DEFAULT_CONCEPT_REGISTRY_PATH,
) -> tuple[Any, ...]:
    """Validate all processed records and return an immutable tuple."""
    record_tuple = tuple(records)
    topic_keys = (
        frozenset(canonical_topics)
        if canonical_topics is not None
        else load_canonical_topic_keys(registry_path)
    )
    seen_record_ids: set[str] = set()

    for index, record in enumerate(record_tuple):
        record_id = _required_non_empty_string(record, "record_id", index)
        if record_id in seen_record_ids:
            raise MetadataValidationError(f"record_id must be unique: {record_id}")
        seen_record_ids.add(record_id)

        metadata = getattr(record, "metadata", None)
        if not isinstance(metadata, Mapping):
            raise MetadataValidationError(f"{record_id} metadata must be a mapping")

        validate_processed_question_metadata(
            metadata,
            canonical_topics=topic_keys,
            record_id=record_id,
        )

    return record_tuple


def validate_processed_question_metadata(
    metadata: Mapping[str, Any],
    *,
    canonical_topics: Iterable[str],
    record_id: str = "record",
) -> None:
    """Validate the retrieval metadata required for one processed question."""
    metadata_fields = frozenset(metadata)
    if metadata_fields != REQUIRED_METADATA_FIELDS:
        missing = sorted(REQUIRED_METADATA_FIELDS - metadata_fields)
        extra = sorted(metadata_fields - REQUIRED_METADATA_FIELDS)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"extra {extra}")
        raise MetadataValidationError(f"{record_id} metadata fields are invalid: {', '.join(details)}")

    _require_allowed_value(metadata, "subject", ALLOWED_SUBJECTS, record_id)
    _require_allowed_value(metadata, "difficulty", ALLOWED_DIFFICULTIES, record_id)
    _require_allowed_value(metadata, "exam_type", ALLOWED_EXAM_TYPES, record_id)
    _require_allowed_value(metadata, "academic_stage", ALLOWED_ACADEMIC_STAGES, record_id)

    topic = metadata["topic"]
    if not isinstance(topic, str) or not topic.strip():
        raise MetadataValidationError(f"{record_id} topic must be a non-empty string")
    if topic not in frozenset(canonical_topics):
        raise MetadataValidationError(f"{record_id} topic is not canonical: {topic}")

    has_worked_solution = metadata["has_worked_solution"]
    if not isinstance(has_worked_solution, bool):
        raise MetadataValidationError(f"{record_id} has_worked_solution must be a boolean")

    year = metadata["year"]
    if not isinstance(year, int) or isinstance(year, bool) or year < 1900:
        raise MetadataValidationError(f"{record_id} year must be an integer >= 1900")


def _required_non_empty_string(record: Any, field_name: str, index: int) -> str:
    value = getattr(record, field_name, None)
    if not isinstance(value, str) or not value.strip():
        raise MetadataValidationError(f"record at index {index} must have {field_name}")
    return value


def _require_allowed_value(
    metadata: Mapping[str, Any],
    field_name: str,
    allowed_values: frozenset[str],
    record_id: str,
) -> None:
    value = metadata[field_name]
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise MetadataValidationError(f"{record_id} {field_name} must be one of: {allowed}")
