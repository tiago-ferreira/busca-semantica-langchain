"""Shared pgVector setup for document ingestion and question retrieval."""

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import create_engine, text

from src.config import Settings


class EmbeddingDimensionMismatch(ValueError):
    """Raised when new embeddings do not match the stored collection."""


def create_embeddings(settings: Settings) -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model, google_api_key=settings.gemini_api_key
    )


def get_collection_embedding_dimension(settings: Settings) -> int | None:
    """Return a stored vector's dimension, or None before a collection exists."""
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            table_exists = connection.execute(
                text("SELECT to_regclass('langchain_pg_embedding')")
            ).scalar_one()
            if table_exists is None:
                return None
            return connection.execute(
                text(
                    """
                    SELECT vector_dims(embedding)
                    FROM langchain_pg_embedding AS e
                    JOIN langchain_pg_collection AS c ON c.uuid = e.collection_id
                    WHERE c.name = :collection_name
                    LIMIT 1
                    """
                ),
                {"collection_name": settings.collection_name},
            ).scalar_one_or_none()
    finally:
        engine.dispose()


def replace_vector_collection(
    documents: list[Document],
    settings: Settings,
    embeddings: Embeddings,
) -> PGVector:
    """Validate new vectors before replacing the configured collection."""
    texts = [document.page_content for document in documents]
    if not texts:
        raise ValueError("Cannot ingest a PDF without extractable text.")

    vectors = embeddings.embed_documents(texts)
    if len(vectors) != len(texts) or not vectors:
        raise ValueError("Embedding provider returned an incomplete result.")
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1 or 0 in dimensions:
        raise ValueError("Embedding provider returned inconsistent vector dimensions.")

    new_dimension = dimensions.pop()
    existing_dimension = get_collection_embedding_dimension(settings)
    if existing_dimension is not None and existing_dimension != new_dimension:
        raise EmbeddingDimensionMismatch(
            f"Collection '{settings.collection_name}' stores "
            f"{existing_dimension}-dimensional embeddings, but model "
            f"'{settings.embedding_model}' returned {new_dimension}-dimensional "
            "embeddings. Remove the collection or PostgreSQL volume before "
            "re-ingesting with this model."
        )

    return PGVector.from_embeddings(
        text_embeddings=list(zip(texts, vectors)),
        embedding=embeddings,
        metadatas=[document.metadata for document in documents],
        collection_name=settings.collection_name,
        connection=settings.database_url,
        pre_delete_collection=True,
    )


def open_vector_collection(settings: Settings, embeddings: Embeddings) -> PGVector:
    return PGVector(
        embeddings=embeddings,
        connection=settings.database_url,
        collection_name=settings.collection_name,
    )
