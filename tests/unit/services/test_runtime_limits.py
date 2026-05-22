import pytest

from app.api.v1.routes.neural_chat import neural_chat
from app.schemas.responses import SabiNeuralResponse
from app.services.runtime_limits import (
    RequestAdmissionRejected,
    WorkerAdmissionGuard,
    admit_request,
    get_request_admission_guard,
)
from tests.unit.services.test_tutor_engine import build_request


def test_worker_admission_guard_rejects_when_capacity_is_exhausted():
    guard = WorkerAdmissionGuard(max_concurrent=1)

    with guard.acquire(timeout_seconds=0):
        with pytest.raises(RequestAdmissionRejected):
            with guard.acquire(timeout_seconds=0):
                pass


def test_worker_admission_guard_releases_capacity_after_context_exit():
    guard = WorkerAdmissionGuard(max_concurrent=1)

    with guard.acquire(timeout_seconds=0):
        pass

    with guard.acquire(timeout_seconds=0):
        pass


def test_admit_request_uses_shared_per_limit_guard():
    with admit_request(max_concurrent=1, timeout_seconds=0):
        with pytest.raises(RequestAdmissionRejected):
            with admit_request(max_concurrent=1, timeout_seconds=0):
                pass


def test_neural_chat_returns_node_compatible_fallback_when_admission_is_exhausted(monkeypatch):
    monkeypatch.setenv("REQUEST_ADMISSION_MAX_CONCURRENT", "1")
    monkeypatch.setenv("REQUEST_ADMISSION_QUEUE_TIMEOUT_SECONDS", "0")
    request = build_request()
    request.request_metadata.uuid_transaction_id = "phase4-saturated"
    registry_snapshot = {
        "version": "test",
        "canonical_keys": {
            "algebra": {"parent_key": None},
            "linear_equations": {"parent_key": "algebra"},
        },
    }
    guard = get_request_admission_guard(1)

    with guard.acquire(timeout_seconds=0):
        response = neural_chat(
            request,
            registry_snapshot=registry_snapshot,
            collections=None,
            embed_query=None,
            completion_callable=None,
        )

    SabiNeuralResponse.model_validate(response)
    assert response["request_id"] == "phase4-saturated"
    assert response["system_metadata"]["pipeline_status"] == "admission_rejected"
    assert (
        response["system_metadata"]["llm_fallback_reason"]
        == "request_admission_capacity_exhausted"
    )
