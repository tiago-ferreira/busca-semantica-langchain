import os
from uuid import uuid4

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from unittest.mock import Mock

from src.config import Settings
from src.ingest import load_and_split_pdf
from src.search import answer_question
from src.vector_store import (
    get_collection_embedding_dimension,
    replace_vector_collection,
)

pytestmark = pytest.mark.integration


class FixedEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


def test_generated_pdf_ingests_and_retrieves_from_pgvector(tmp_path):
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/semantic_search",
    )
    engine = create_engine(database_url, connect_args={"connect_timeout": 1})
    try:
        with engine.connect() as connection:
            has_vector_extension = connection.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            ).scalar_one()
    except OperationalError as error:
        pytest.skip(f"PostgreSQL is not running at the configured DATABASE_URL: {error}")
    finally:
        engine.dispose()

    assert has_vector_extension, "Enable the pgvector extension before running this test."

    pdf_path = tmp_path / "document.pdf"
    pdf = canvas.Canvas(str(pdf_path))
    pdf.drawString(72, 720, "A Empresa SuperTechIABrazil teve faturamento de 10 milhões de reais.")
    pdf.save()
    documents = load_and_split_pdf(pdf_path)

    settings = Settings(
        gemini_api_key="mocked",
        database_url=database_url,
        embedding_model="fixed-test-embeddings",
        chat_model="mocked-chat",
        collection_name=f"integration-{uuid4().hex}",
    )
    embeddings = FixedEmbeddings()
    vector_store = replace_vector_collection(documents, settings, embeddings)
    model = Mock()
    model.invoke.return_value = AIMessage(
        content="O faturamento foi de 10 milhões de reais."
    )

    try:
        assert get_collection_embedding_dimension(settings) == 3
        answer = answer_question(
            "Qual o faturamento da Empresa SuperTechIABrazil?",
            settings,
            vector_store=vector_store,
            chat_model=model,
        )
        assert answer == "O faturamento foi de 10 milhões de reais."
        prompt = model.invoke.call_args.args[0][0].content
        assert "10 milhões de reais" in prompt
    finally:
        vector_store.delete_collection()
