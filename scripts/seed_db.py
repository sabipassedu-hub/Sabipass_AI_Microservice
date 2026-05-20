"""Seed local Chroma collections from mock processed ingestion data."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipelines.ingestion.chroma_seed import seed_demo_collections


def main() -> int:
    result = seed_demo_collections()
    print(f"Seeded {result.exam_bank.records_seeded} records into exam_bank.")
    print(f"Seeded {result.curriculum_vault.records_seeded} records into curriculum_vault.")
    print(f"Seeded {result.analogy_sandbox.records_seeded} records into analogy_sandbox.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
