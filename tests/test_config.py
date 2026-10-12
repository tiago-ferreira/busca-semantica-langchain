import pytest

from src.config import ConfigurationError, load_settings


def test_loads_required_and_default_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://localhost/test")
    for name in (
        "GEMINI_EMBEDDING_MODEL",
        "GEMINI_CHAT_MODEL",
        "PGVECTOR_COLLECTION",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings(env_file=None)

    assert settings.gemini_api_key == "test-key"
    assert settings.database_url == "postgresql+psycopg://localhost/test"
    assert settings.embedding_model == "models/gemini-embedding-001"
    assert settings.chat_model == "gemini-2.5-flash"
    assert settings.collection_name == "pdf_documents"


@pytest.mark.parametrize(
    ("api_key", "database_url", "missing_name"),
    [
        ("", "postgresql://localhost/test", "GEMINI_API_KEY"),
        ("test-key", "", "DATABASE_URL"),
        ("", "", "GEMINI_API_KEY, DATABASE_URL"),
    ],
)
def test_reports_missing_required_settings(
    monkeypatch, api_key, database_url, missing_name
):
    monkeypatch.setenv("GEMINI_API_KEY", api_key)
    monkeypatch.setenv("DATABASE_URL", database_url)

    with pytest.raises(ConfigurationError, match=missing_name):
        load_settings(env_file=None)
