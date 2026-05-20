"""Layer 6 model routing for provider-agnostic LiteLLM execution.

Purpose: choose model names, history budgets, and execution paths from
environment-configured tier settings. Constraints from CODEX_MASTER_DIRECTIVE:
no provider SDK imports, no hard-coded provider choice, LiteLLM-only execution,
free tier single-pass only, premium tier may use two-pass, and efficiency mode
is a user-controlled downgrade rather than an automatic system decision.
"""

from dataclasses import dataclass
from typing import Literal, cast

from app.core.config import get_history_turn_limit, read_required_env


ExecutionPath = Literal["single_pass", "two_pass"]
ProviderInterface = Literal["litellm"]
Tier = Literal["free", "premium"]


@dataclass(frozen=True)
class ModelRoute:
    """Provider-agnostic route metadata for later LiteLLM execution."""

    provider_interface: ProviderInterface
    model_env_var: str
    model_name: str
    max_history_turns: int
    execution_path: ExecutionPath


def select_model_route(
    *,
    tier: str,
    efficiency_mode: bool,
    requested_execution_path: ExecutionPath,
) -> ModelRoute:
    """Select a tier-aware, efficiency-aware model route."""
    normalized_tier = _normalize_tier(tier)

    if efficiency_mode:
        return _build_route(
            tier=normalized_tier,
            efficiency_mode=efficiency_mode,
            model_env_var="EFFICIENCY_MODE_MODEL",
            execution_path=_downgrade_execution_path(requested_execution_path),
        )

    if normalized_tier == "free":
        return _build_route(
            tier=normalized_tier,
            efficiency_mode=efficiency_mode,
            model_env_var="TIER_FREE_MODEL",
            execution_path="single_pass",
        )

    return _build_route(
        tier=normalized_tier,
        efficiency_mode=efficiency_mode,
        model_env_var="TIER_PREMIUM_MODEL",
        execution_path=requested_execution_path,
    )


def _normalize_tier(tier: str) -> Tier:
    normalized = tier.strip().lower()
    if normalized not in {"free", "premium"}:
        raise ValueError("tier must be 'free' or 'premium'")
    return cast(Tier, normalized)


def _downgrade_execution_path(execution_path: ExecutionPath) -> ExecutionPath:
    if execution_path == "two_pass":
        return "single_pass"
    return "single_pass"


def _build_route(
    *,
    tier: Tier,
    efficiency_mode: bool,
    model_env_var: str,
    execution_path: ExecutionPath,
) -> ModelRoute:
    return ModelRoute(
        provider_interface="litellm",
        model_env_var=model_env_var,
        model_name=read_required_env(model_env_var),
        max_history_turns=get_history_turn_limit(tier, efficiency_mode),
        execution_path=execution_path,
    )
