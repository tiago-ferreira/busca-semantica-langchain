from unittest.mock import Mock

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from src.config import Settings
from src.search import (
    ANSWER_PROMPT_TEMPLATE,
    FALLBACK_ANSWER,
    RESULTS_LIMIT,
    answer_question,
)


def test_retrieves_ten_chunks_and_uses_only_the_retrieved_context(monkeypatch):
    from src import search

    settings = Settings(
        gemini_api_key="test-key",
        database_url="postgresql+psycopg://localhost/test",
        embedding_model="test-embeddings",
        chat_model="test-chat",
        collection_name="test-collection",
    )
    documents = [
        (Document(page_content=f"chunk {index}"), 0.1) for index in range(10)
    ]
    store = Mock()
    store.similarity_search_with_score.return_value = documents
    embeddings = Mock()
    monkeypatch.setattr(search, "create_embeddings", lambda _: embeddings)
    model = Mock()
    model.invoke.return_value = AIMessage(content="Resposta baseada nos chunks.")

    answer = answer_question(
        "Qual informação está no PDF?",
        settings,
        vector_store=store,
        chat_model=model,
    )

    assert answer == "Resposta baseada nos chunks."
    store.similarity_search_with_score.assert_called_once_with(
        "Qual informação está no PDF?", k=RESULTS_LIMIT
    )
    messages = model.invoke.call_args.args[0]
    assert "chunk 0" in messages[0].content
    assert "chunk 9" in messages[0].content
    assert "Qual informação está no PDF?" in messages[0].content
    assert "Nunca invente ou use conhecimento externo." in messages[0].content


def test_returns_exact_fallback_without_calling_chat_model(monkeypatch):
    from src import search

    settings = Settings(
        gemini_api_key="test-key",
        database_url="postgresql+psycopg://localhost/test",
        embedding_model="test-embeddings",
        chat_model="test-chat",
        collection_name="test-collection",
    )
    store = Mock()
    store.similarity_search_with_score.return_value = []
    monkeypatch.setattr(search, "create_embeddings", lambda _: Mock())
    model = Mock()

    answer = answer_question(
        "Pergunta sem contexto", settings, vector_store=store, chat_model=model
    )

    assert answer == FALLBACK_ANSWER
    model.invoke.assert_not_called()


def test_creates_gemini_chat_model_with_configured_model_and_key(monkeypatch):
    from src import search

    settings = Settings(
        gemini_api_key="test-key",
        database_url="postgresql+psycopg://localhost/test",
        embedding_model="test-embeddings",
        chat_model="test-chat",
        collection_name="test-collection",
    )
    store = Mock()
    store.similarity_search_with_score.return_value = [
        (Document(page_content="context"), 0.1)
    ]
    model = Mock()
    model.invoke.return_value = AIMessage(content="Answer")
    constructor = Mock(return_value=model)
    monkeypatch.setattr(search, "ChatGoogleGenerativeAI", constructor)

    assert answer_question("Question", settings, vector_store=store) == "Answer"
    constructor.assert_called_once_with(
        model=settings.chat_model,
        google_api_key=settings.gemini_api_key,
    )


def test_prompt_includes_exact_required_fallback():
    assert FALLBACK_ANSWER == "Não tenho informações necessárias para responder sua pergunta."
    assert ANSWER_PROMPT_TEMPLATE.count(FALLBACK_ANSWER) == 4


def test_rejects_empty_question():
    import pytest

    with pytest.raises(ValueError, match="Question cannot be empty"):
        answer_question("  ", settings=Mock())
