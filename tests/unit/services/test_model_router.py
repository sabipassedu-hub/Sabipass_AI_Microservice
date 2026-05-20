import pytest

from app.services.model_router import ModelRoute, select_model_route


def test_free_tier_route_uses_litellm_and_free_model_env_var(monkeypatch):
    monkeypatch.setenv("TIER_FREE_MODEL", "free-tier-test-model")

    route = select_model_route(
        tier="free",
        efficiency_mode=False,
        requested_execution_path="two_pass",
    )

    assert route == ModelRoute(
        provider_interface="litellm",
        model_env_var="TIER_FREE_MODEL",
        model_name="free-tier-test-model",
        max_history_turns=1,
        execution_path="single_pass",
    )


def test_premium_route_preserves_two_pass_request(monkeypatch):
    monkeypatch.setenv("TIER_PREMIUM_MODEL", "premium-tier-test-model")

    route = select_model_route(
        tier="premium",
        efficiency_mode=False,
        requested_execution_path="two_pass",
    )

    assert route.provider_interface == "litellm"
    assert route.model_env_var == "TIER_PREMIUM_MODEL"
    assert route.model_name == "premium-tier-test-model"
    assert route.max_history_turns == 3
    assert route.execution_path == "two_pass"


def test_efficiency_mode_uses_efficiency_model_and_downgrades_execution(monkeypatch):
    monkeypatch.setenv("EFFICIENCY_MODE_MODEL", "efficiency-test-model")

    route = select_model_route(
        tier="premium",
        efficiency_mode=True,
        requested_execution_path="two_pass",
    )

    assert route.provider_interface == "litellm"
    assert route.model_env_var == "EFFICIENCY_MODE_MODEL"
    assert route.model_name == "efficiency-test-model"
    assert route.max_history_turns == 0
    assert route.execution_path == "single_pass"


def test_model_router_rejects_unknown_tier():
    with pytest.raises(ValueError, match="tier"):
        select_model_route(
            tier="enterprise",
            efficiency_mode=False,
            requested_execution_path="single_pass",
        )


def test_model_router_uses_safe_default_model_when_env_is_missing(monkeypatch):
    monkeypatch.delenv("TIER_FREE_MODEL", raising=False)

    route = select_model_route(
        tier="free",
        efficiency_mode=False,
        requested_execution_path="single_pass",
    )

    assert route.model_env_var == "TIER_FREE_MODEL"
    assert route.model_name == "groq/llama-3.1-8b-instant"


def test_model_router_applies_env_configured_history_limit(monkeypatch):
    monkeypatch.setenv("TIER_PREMIUM_MODEL", "premium-tier-test-model")
    monkeypatch.setenv("TIER_PREMIUM_MAX_HISTORY_TURNS", "5")

    route = select_model_route(
        tier="premium",
        efficiency_mode=False,
        requested_execution_path="single_pass",
    )

    assert route.max_history_turns == 5
