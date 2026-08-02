from __future__ import annotations

import pytest

from f1_project.config import Settings


def test_settings_from_env_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENF1_BASE_URL", raising=False)
    monkeypatch.delenv("OPENF1_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENF1_MAX_RETRIES", raising=False)

    settings = Settings.from_env()

    assert settings.base_url == "https://api.openf1.org/v1/"
    assert settings.timeout_seconds == 10.0
    assert settings.max_retries == 3


def test_settings_from_env_reads_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENF1_BASE_URL", "https://example.test/v1/")
    monkeypatch.setenv("OPENF1_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("OPENF1_MAX_RETRIES", "1")

    settings = Settings.from_env()

    assert settings.base_url == "https://example.test/v1/"
    assert settings.timeout_seconds == 5.0
    assert settings.max_retries == 1
