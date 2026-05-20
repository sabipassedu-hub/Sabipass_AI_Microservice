import json
from pathlib import Path

from app.db.chroma import EXAM_BANK, initialize_chroma
from app.rag.embeddings import embed_query_text
from app.rag.retriever import retrieve_from_collection
from pipelines.ingestion.chroma_seed import seed_mock_exam_bank


REPO_ROOT = Path(__file__).resolve().parents[2]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"
GOLDEN_SET_PATH = Path(__file__).with_name("retrieval_golden_set.json")


def test_retrieval_golden_set_hits_expected_mock_exam_chunks(tmp_path: Path):
    seed_mock_exam_bank(MOCK_RAW_DIR, storage_path=tmp_path)
    collection = initialize_chroma(tmp_path)[EXAM_BANK]
    golden_cases = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))

    for case in golden_cases:
        hits = retrieve_from_collection(
            collection,
            embed_query_text(case["query"]),
            metadata_filter={
                "topic": case["topic"],
                "exam_type": "WAEC",
                "academic_stage": "senior_secondary",
            },
            top_k=3,
        )

        assert hits, case
        assert hits[0].metadata["chunk_id"] == case["expected_chunk_id"]
