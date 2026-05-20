from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tier_free_model: str = "groq/llama-3.1-8b-instant"
    tier_premium_model: str = "groq/llama-3.3-70b-versatile"
    efficiency_mode_model: str = "groq/llama-3.1-8b-instant"
    tier_free_max_history_turns: int = Field(default=1, ge=0)
    tier_premium_max_history_turns: int = Field(default=3, ge=0)
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    sabi_bootstrap_mock_data: bool = True
    sympy_timeout_ms: int = Field(default=250, ge=1)
    sympy_max_workers: int = Field(default=1, ge=1)


_ENV_FIELD_BY_NAME = {
    "TIER_FREE_MODEL": "tier_free_model",
    "TIER_PREMIUM_MODEL": "tier_premium_model",
    "EFFICIENCY_MODE_MODEL": "efficiency_mode_model",
}


def get_settings() -> Settings:
    return Settings()


def read_required_env(name: str) -> str:
    settings = get_settings()
    field_name = _ENV_FIELD_BY_NAME.get(name)
    if field_name is None:
        raise RuntimeError(f"Required environment variable {name} is not configured")

    value = str(getattr(settings, field_name, "")).strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")

    return value


def read_non_negative_int_env(name: str, default: int) -> int:
    settings = get_settings()
    field_name = name.lower()
    if hasattr(settings, field_name):
        return max(0, int(getattr(settings, field_name)))
    return max(0, default)


def get_history_turn_limit(tier: str, efficiency_mode: bool) -> int:
    settings = get_settings()
    if efficiency_mode:
        return 0

    if tier == "premium":
        return settings.tier_premium_max_history_turns

    return settings.tier_free_max_history_turns
