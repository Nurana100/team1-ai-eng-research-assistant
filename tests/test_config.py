"""Tests for src/config.py — typed settings loaded from environment."""

from src.config import Settings, get_settings


def test_settings_have_sane_defaults():
    settings = Settings()
    assert settings.llm_provider
    assert settings.llm_model
    assert settings.log_level == "INFO"
    assert settings.cache_ttl_seconds == 86400
    assert settings.max_parallel == 5


def test_settings_reads_env_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-3.6-flash")

    settings = Settings()

    assert settings.llm_provider == "gemini"
    assert settings.llm_model == "gemini-3.6-flash"


def test_settings_ignores_unknown_env_keys(monkeypatch):
    monkeypatch.setenv("SOME_RANDOM_UNUSED_KEY", "whatever")

    settings = Settings()

    assert settings is not None


def test_get_settings_returns_settings_instance():
    settings = get_settings()

    assert isinstance(settings, Settings)


def test_settings_api_keys_default_empty(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key == ""
    assert settings.openai_api_key == ""
    assert settings.google_api_key == ""