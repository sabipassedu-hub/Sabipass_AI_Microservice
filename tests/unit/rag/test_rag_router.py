import json
from pathlib import Path
from typing import Any

import pytest

from app.db.chroma import EXAM_BANK, initialize_chroma
from app.rag.retriever import RetrievalHit
from app.schemas.requests import NeuralChatRequest
from app.schemas.strategy import ModelStrategy, PedagogyStrategy, RagStrategy, StateStrategy
from app.services.rag_router import (
    FallbackSummaryError,
    build_precision_rag_query,
    load_fallback_summary,
    retrieve_context_for_strategy,
)
from app.services.strategy.compiler import compile_state_strategy


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


class FakeCollection:
    name = "exam_bank"

    def __init__(self) -> None:
        self.query_kwargs: dict[str, Any] | None = None

    def query(self, **kwargs) -> dict[str, Any]:
        self.query_kwargs = kwargs
        return {
            "ids": [["waec_2020_math_q12"]],
            "documents": [["Solve 2x + 4 = 10 by isolating x."]],
            "metadatas": [
                [
                    {
                        "source_type": "worked_solution",
                        "doc_id": "waec_2020_math_q12",
                        "chunk_id": "0",
                        "subject": "mathematics",
                        "topic": "linear_equations",
                        "exam_type": "WAEC",
                        "academic_stage": "senior_secondary",
                        "year": 2020,
                        "has_worked_solution": True,
                    }
                ]
            ],
            "distances": [[0.0]],
        }


def build_strategy(rag_strategy: RagStrategy) -> StateStrategy:
    return StateStrategy(
        execution_path="single_pass",
        complexity_score=2,
        normalized_concept=rag_strategy.query_concept_key,
        normalization_confidence=0.95,
        normalization_status="strict",
        rag_strategy=rag_strategy,
        pedagogy_strategy=PedagogyStrategy(
            teaching_mode="direct_instruction",
            response_format="text_only",
            intent_type="explanation",
            urgency="normal",
        ),
        model_strategy=ModelStrategy(
            tier="free",
            efficiency_mode=False,
            execution_path="single_pass",
        ),
    )


def precision_strategy() -> StateStrategy:
    return build_strategy(
        RagStrategy(
            mode="precision",
            target_collection="exam_bank",
            query_concept_key="linear_equations",
            filters=(
                ("subject", "mathematics"),
                ("topic", "linear_equations"),
                ("exam_type", "WAEC"),
                ("academic_stage", "senior_secondary"),
            ),
            top_k=3,
        )
    )


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def build_request(raw_whiteboard_input: str) -> NeuralChatRequest:
    return NeuralChatRequest.model_validate(
        {
            "request_metadata": {
                "uuid_transaction_id": "txn-rag-router-test-001",
                "timestamp": "2026-05-19T12:00:00Z",
                "device_latency_ms": 120,
            },
            "student_identity": {
                "student_db_id": "student_rag_router_001",
                "tier": "free",
                "academic_scope": "senior_secondary",
                "exam_target": "WAEC",
            },
            "efficiency_mode": False,
            "app_execution_mode": "exam_prep",
            "cognitive_aptitude_profile": {
                "regression_slope": 0.2,
                "scaffolding_flag": "low",
                "complexity_tolerance": "medium",
                "knowledge_decay_params": "medium",
            },
            "emotional_telemetry": {
                "rage_clicks": [],
                "caps_lock_aggression": [],
                "detected_frustration_signals": [],
                "sentiment_trends": "stable",
                "latency_focus_integrity": 1.0,
            },
            "current_interaction_context": {
                "raw_whiteboard_input": raw_whiteboard_input,
                "topic_node": "",
                "history_tokens": [],
                "errors_on_same_concept_space": 0,
            },
            "historical_mastery_map": {
                "active_weakness_arrays": ["algebra"],
                "passed_topics_arrays": [],
            },
        }
    )


def test_precision_mode_uses_strategy_collection_filters_and_canonical_query():
    collection = FakeCollection()
    embedded_queries: list[str] = []

    def embed_query(query_text: str) -> list[float]:
        embedded_queries.append(query_text)
        return [1.0, 0.0, 0.0]

    context = retrieve_context_for_strategy(
        precision_strategy(),
        collections={"exam_bank": collection},
        embed_query=embed_query,
    )

    assert embedded_queries == ["linear_equations"]
    assert collection.query_kwargs == {
        "query_embeddings": [[1.0, 0.0, 0.0]],
        "n_results": 3,
        "include": ["documents", "metadatas", "distances"],
        "where": {
            "$and": [
                {"subject": "mathematics"},
                {"topic": "linear_equations"},
                {"exam_type": "WAEC"},
                {"academic_stage": "senior_secondary"},
            ]
        },
    }
    assert context.mode == "precision"
    assert len(context.hits) == 1
    assert isinstance(context.hits[0], RetrievalHit)
    assert context.source_tags == (context.hits[0].source_tag,)
    assert context.source_tags[0].startswith("src:v1;collection=exam_bank")
    assert "Solve 2x + 4 = 10" in context.context_text


def test_precision_mode_filters_chroma_hits_and_source_tags_every_hit(tmp_path: Path):
    collections = initialize_chroma(tmp_path)
    collection = collections[EXAM_BANK]
    collection.add(
        ids=["waec_math_linear_001", "jamb_math_linear_001"],
        documents=[
            "Solve 2x + 4 = 10 by isolating x.",
            "Solve y + 3 = 7 by subtracting 3.",
        ],
        embeddings=[
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        metadatas=[
            {
                "source_type": "worked_solution",
                "doc_id": "waec_math_linear_001",
                "chunk_id": "0",
                "subject": "mathematics",
                "topic": "linear_equations",
                "exam_type": "WAEC",
                "academic_stage": "senior_secondary",
                "year": 2020,
                "has_worked_solution": True,
            },
            {
                "source_type": "worked_solution",
                "doc_id": "jamb_math_linear_001",
                "chunk_id": "0",
                "subject": "mathematics",
                "topic": "linear_equations",
                "exam_type": "JAMB",
                "academic_stage": "senior_secondary",
                "year": 2021,
                "has_worked_solution": True,
            },
        ],
    )

    context = retrieve_context_for_strategy(
        precision_strategy(),
        collections=collections,
        embed_query=lambda query_text: [1.0, 0.0, 0.0],
    )

    assert [hit.document_id for hit in context.hits] == ["waec_math_linear_001"]
    assert context.source_tags == (
        "src:v1;collection=exam_bank;source_type=worked_solution;"
        "doc_id=waec_math_linear_001;chunk_id=0;subject=mathematics;"
        "topic=linear_equations;exam_type=waec;academic_stage=senior_secondary;"
        "year=2020;has_worked_solution=true;rank=1",
    )
    assert context.source_tags[0] in context.context_text
    assert "jamb_math_linear_001" not in context.context_text


def test_rag_query_uses_normalized_concept_from_compiled_pidgin_prompt():
    raw_input = "Abeg explain how i go find x for this equation."
    strategy = compile_state_strategy(build_request(raw_input), registry_snapshot=load_registry())

    rag_query = build_precision_rag_query(strategy)

    assert strategy.normalized_concept == "linear_equations"
    assert rag_query.query_concept_key == "linear_equations"
    assert rag_query.query_concept_key != raw_input
    assert rag_query.metadata_filter["topic"] == "linear_equations"


def test_fallback_mode_loads_summary_without_vector_search(tmp_path: Path):
    fallback_dir = tmp_path / "fallback"
    fallback_dir.mkdir()
    summary_text = "Use foundational mathematics steps and ask for the full question when needed."
    (fallback_dir / "general_mathematics_v1_summary.json").write_text(
        json.dumps(
            {
                "concept_key": "general_mathematics_v1",
                "summary_text": summary_text,
                "token_count": len(summary_text.split()),
                "version": "1.0",
            }
        ),
        encoding="utf-8",
    )

    def forbidden_embed_query(query_text: str) -> list[float]:
        raise AssertionError("fallback mode must not run vector search")

    context = retrieve_context_for_strategy(
        build_strategy(
            RagStrategy(
                mode="fallback",
                target_collection=None,
                query_concept_key="general_mathematics",
                filters=(),
                top_k=0,
            )
        ),
        collections={},
        embed_query=forbidden_embed_query,
        fallback_dir=fallback_dir,
    )

    assert context.mode == "fallback"
    assert context.context_text == summary_text
    assert context.hits == ()
    assert context.source_tags == ()
    assert context.fallback_summary is not None
    assert context.fallback_summary.concept_key == "general_mathematics_v1"


def test_fallback_loader_rejects_summary_over_token_budget(tmp_path: Path):
    fallback_dir = tmp_path / "fallback"
    fallback_dir.mkdir()
    summary_text = " ".join(["word"] * 601)
    (fallback_dir / "general_mathematics_v1_summary.json").write_text(
        json.dumps(
            {
                "concept_key": "general_mathematics_v1",
                "summary_text": summary_text,
                "token_count": 601,
                "version": "1.0",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(FallbackSummaryError, match="600 tokens"):
        load_fallback_summary("general_mathematics", fallback_dir=fallback_dir)
