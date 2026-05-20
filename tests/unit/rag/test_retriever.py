from pathlib import Path

import pytest

from app.db.chroma import EXAM_BANK, initialize_chroma
from app.rag.retriever import build_source_tag, retrieve_from_collection


def _seed_exam_bank(tmp_path: Path):
    collection = initialize_chroma(tmp_path)[EXAM_BANK]
    collection.add(
        ids=["waec_2020_math_q12", "waec_2021_biology_q03"],
        documents=[
            "Solve 2x + 4 = 10 by isolating x.",
            "Photosynthesis converts light energy into chemical energy.",
        ],
        embeddings=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        metadatas=[
            {
                "source_type": "worked_solution",
                "doc_id": "waec_2020_math_q12",
                "chunk_id": "0",
                "subject": "mathematics",
                "topic": "linear_equations",
                "exam_type": "WAEC",
                "academic_stage": "senior_secondary_2",
                "year": 2020,
                "has_worked_solution": True,
            },
            {
                "source_type": "past_question",
                "doc_id": "waec_2021_biology_q03",
                "chunk_id": "0",
                "subject": "biology",
                "topic": "photosynthesis",
                "exam_type": "WAEC",
                "academic_stage": "senior_secondary_2",
                "year": 2021,
                "has_worked_solution": False,
            },
        ],
    )
    return collection


def test_retrieves_from_one_collection_with_metadata_filter(tmp_path: Path):
    collection = _seed_exam_bank(tmp_path)

    hits = retrieve_from_collection(
        collection,
        query_embedding=[1.0, 0.0, 0.0],
        metadata_filter={"topic": "linear_equations"},
        top_k=2,
    )

    assert len(hits) == 1
    assert hits[0].collection_name == EXAM_BANK
    assert hits[0].document_id == "waec_2020_math_q12"
    assert hits[0].text == "Solve 2x + 4 = 10 by isolating x."
    assert hits[0].metadata["topic"] == "linear_equations"


def test_converts_cosine_distance_to_clamped_confidence(tmp_path: Path):
    collection = _seed_exam_bank(tmp_path)

    hits = retrieve_from_collection(
        collection,
        query_embedding=[1.0, 0.0, 0.0],
        metadata_filter={"topic": "linear_equations"},
        top_k=1,
    )

    assert hits[0].distance == 0.0
    assert hits[0].confidence == 1.0


def test_returns_empty_list_when_filter_has_no_matches(tmp_path: Path):
    collection = _seed_exam_bank(tmp_path)

    hits = retrieve_from_collection(
        collection,
        query_embedding=[1.0, 0.0, 0.0],
        metadata_filter={"exam_type": "JAMB"},
        top_k=2,
    )

    assert hits == []


def test_source_tag_has_stable_parseable_fields():
    source_tag = build_source_tag(
        collection_name=EXAM_BANK,
        document_id="waec_2020_math_q12",
        metadata={
            "source_type": "worked_solution",
            "doc_id": "waec_2020_math_q12",
            "chunk_id": "0",
            "subject": "Mathematics",
            "topic": "Linear Equations",
            "exam_type": "WAEC",
            "academic_stage": "senior_secondary_2",
            "year": 2020,
            "has_worked_solution": True,
        },
        rank=1,
    )

    assert source_tag == (
        "src:v1;collection=exam_bank;source_type=worked_solution;"
        "doc_id=waec_2020_math_q12;chunk_id=0;subject=mathematics;"
        "topic=linear_equations;exam_type=waec;"
        "academic_stage=senior_secondary_2;year=2020;"
        "has_worked_solution=true;rank=1"
    )
    assert ";" in source_tag
    assert all("=" in field for field in source_tag.split(";")[1:])


def test_source_tag_sanitizes_unsafe_metadata_values():
    source_tag = build_source_tag(
        collection_name="exam=bank",
        document_id="doc;id",
        metadata={
            "topic": "linear;equations=true",
            "has_worked_solution": False,
        },
        rank=2,
    )

    assert "exam=bank" not in source_tag
    assert "doc;id" not in source_tag
    assert "linear;equations=true" not in source_tag
    assert "has_worked_solution=false" in source_tag


@pytest.mark.parametrize("top_k", [0, -1])
def test_rejects_invalid_top_k(tmp_path: Path, top_k: int):
    collection = _seed_exam_bank(tmp_path)

    with pytest.raises(ValueError, match="top_k"):
        retrieve_from_collection(
            collection,
            query_embedding=[1.0, 0.0, 0.0],
            top_k=top_k,
        )


def test_rejects_empty_query_embedding(tmp_path: Path):
    collection = _seed_exam_bank(tmp_path)

    with pytest.raises(ValueError, match="query_embedding"):
        retrieve_from_collection(collection, query_embedding=[])
