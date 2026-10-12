"""Shared environment configuration for ingestion and search."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    database_url: str
    embedding_model: str
    chat_model: str
    collection_name: str


class ConfigurationError(ValueError):
    """Raised when a required application setting is missing."""


def load_settings(env_file: Path | None = None) -> Settings:
    """Load environment settings, reporting all missing required values."""
    load_dotenv(dotenv_path=env_file, override=False)

    required = {
        "GEMINI_API_KEY": "gemini_api_key",
        "DATABASE_URL": "database_url",
    }
    values = {name: os.getenv(name, "").strip() for name in required}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ConfigurationError(
            "Variável(is) de ambiente obrigatória(s) não configurada(s): "
            + ", ".join(missing)
        )

    return Settings(
        gemini_api_key=values["GEMINI_API_KEY"],
        database_url=values["DATABASE_URL"],
        embedding_model=os.getenv(
            "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
        ).strip(),
        chat_model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash").strip(),
        collection_name=os.getenv("PGVECTOR_COLLECTION", "pdf_documents").strip(),
    )
