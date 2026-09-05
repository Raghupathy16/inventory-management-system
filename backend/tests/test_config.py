"""
Phase 1 tests: configuration loading.

There's no business logic yet to test (that starts Phase 2+), but it's
still worth verifying that our Settings object behaves correctly, since
every other part of the app depends on it working right.
"""

import os

import pytest
from pydantic import ValidationError


def test_settings_load_from_environment(monkeypatch):
    """Settings should read values from environment variables correctly."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")
    monkeypatch.setenv("SECRET_KEY", "test_secret")

    # Import here (after env vars are set) and bypass the lru_cache so we
    # get a fresh instance built from these specific env vars.
    from app.core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.DB_HOST == "localhost"
    assert settings.DB_PORT == 3306
    assert settings.database_url == (
        "mysql+pymysql://test_user:test_pass@localhost:3306/test_db"
    )


def test_settings_missing_required_field_fails_fast(monkeypatch):
    """
    A missing required env var (e.g. DB_PASSWORD) should raise a clear
    validation error at construction time, not fail silently or crash
    later with a confusing DB connection error.
    """
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("SECRET_KEY", "test_secret")

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_uses_pymysql_driver(monkeypatch):
    """
    We specifically require the pymysql driver in the connection string,
    since that's the driver installed in requirements.txt. A typo here
    (e.g. plain 'mysql://') would fail at runtime with a driver-not-found
    error that's confusing for a beginner to debug.
    """
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_NAME", "inventory_db")
    monkeypatch.setenv("DB_USER", "inventory_user")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("SECRET_KEY", "secret_key")

    from app.core.config import Settings

    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("mysql+pymysql://")
