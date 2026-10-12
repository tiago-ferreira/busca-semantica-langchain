from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from src.config import Settings
from src.vector_store import (
    EmbeddingDimensionMismatch,
    create_embeddings,
    replace_vector_collection,
)


@pytest.fixture
def settings():
    return Settings(
        gemini_api_key="test-key",
        database_url="postgresql+psycopg://localhost/test",
        embedding_model="test-embeddings",
        chat_model="test-chat",
        collection_name="test-collection",
    )


def test_replaces_collection_after_embedding_and_dimension_validation(
    monkeypatch, settings
):
    from src import vector_store

    documents = [
        Document(page_content="first", metadata={"page": 0}),
        Document(page_content="second", metadata={"page": 1}),
    ]
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[1.0, 2.0], [3.0, 4.0]]
    monkeypatch.setattr(vector_store, "get_collection_embedding_dimension", lambda _: 2)
    monkeypatch.setattr(vector_store.PGVector, "from_embeddings", Mock(return_value="store"))

    result = replace_vector_collection(documents, settings, embeddings)

    assert result == "store"
    vector_store.PGVector.from_embeddings.assert_called_once_with(
        text_embeddings=[("first", [1.0, 2.0]), ("second", [3.0, 4.0])],
        embedding=embeddings,
        metadatas=[{"page": 0}, {"page": 1}],
        collection_name="test-collection",
        connection=settings.database_url,
        pre_delete_collection=True,
    )


def test_creates_gemini_embeddings_with_configured_model_and_key(monkeypatch, settings):
    from src import vector_store

    constructor = Mock(return_value="embeddings")
    monkeypatch.setattr(vector_store, "GoogleGenerativeAIEmbeddings", constructor)

    assert create_embeddings(settings) == "embeddings"
    constructor.assert_called_once_with(
        model=settings.embedding_model,
        google_api_key=settings.gemini_api_key,
    )


def test_dimension_mismatch_does_not_delete_existing_collection(
    monkeypatch, settings
):
    from src import vector_store

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[1.0, 2.0, 3.0]]
    monkeypatch.setattr(vector_store, "get_collection_embedding_dimension", lambda _: 2)
    write_collection = Mock()
    monkeypatch.setattr(vector_store.PGVector, "from_embeddings", write_collection)

    with pytest.raises(EmbeddingDimensionMismatch, match="Remove the collection"):
        replace_vector_collection(
            [Document(page_content="content")], settings, embeddings
        )

    write_collection.assert_not_called()


def test_rejects_empty_or_invalid_embedding_results(monkeypatch, settings):
    from src import vector_store

    monkeypatch.setattr(vector_store, "get_collection_embedding_dimension", lambda _: None)
    embeddings = Mock()
    embeddings.embed_documents.return_value = []
    with pytest.raises(ValueError, match="incomplete"):
        replace_vector_collection([Document(page_content="content")], settings, embeddings)

    embeddings.embed_documents.return_value = [[1.0], [1.0, 2.0]]
    with pytest.raises(ValueError, match="inconsistent"):
        replace_vector_collection(
            [Document(page_content="one"), Document(page_content="two")],
            settings,
            embeddings,
        )
