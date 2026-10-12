"""Retrieve document context and answer questions about the indexed PDF."""

import sys
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai._common import GoogleGenerativeAIError
from sqlalchemy.exc import SQLAlchemyError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ConfigurationError, Settings, load_settings
from src.vector_store import create_embeddings, open_vector_collection

FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."
RESULTS_LIMIT = 10
ANSWER_PROMPT_TEMPLATE = """CONTEXTO:
{context}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{question}

RESPONDA A "PERGUNTA DO USUÁRIO\""""


def answer_question(
    question: str,
    settings: Settings | None = None,
    *,
    vector_store=None,
    chat_model=None,
) -> str:
    """Answer a question from up to ten retrieved PDF chunks."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    settings = settings or load_settings(Path(__file__).resolve().parents[1] / ".env")
    if vector_store is None:
        embeddings = create_embeddings(settings)
        vector_store = open_vector_collection(settings, embeddings)
    results = vector_store.similarity_search_with_score(question, k=RESULTS_LIMIT)
    context = "\n\n".join(document.page_content for document, _ in results)
    if not context.strip():
        return FALLBACK_ANSWER

    model = chat_model or ChatGoogleGenerativeAI(
        model=settings.chat_model, google_api_key=settings.gemini_api_key
    )
    messages = ChatPromptTemplate.from_template(ANSWER_PROMPT_TEMPLATE).format_messages(
        context=context,
        question=question,
    )
    answer = StrOutputParser().invoke(model.invoke(messages)).strip()
    if not answer:
        raise ValueError("The chat model returned an empty answer.")
    return answer


def main() -> int:
    try:
        answer = answer_question(input("Faça sua pergunta: "))
    except (
        ConfigurationError,
        GoogleGenerativeAIError,
        SQLAlchemyError,
        ValueError,
    ) as error:
        print(f"Falha na busca: {error}", file=sys.stderr)
        return 1

    print(f"RESPOSTA: {answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
