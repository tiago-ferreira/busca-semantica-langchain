"""Interactive terminal chat for the indexed PDF."""

import sys
from pathlib import Path
from typing import Callable

from langchain_google_genai._common import GoogleGenerativeAIError
from sqlalchemy.exc import SQLAlchemyError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ConfigurationError
from src.search import answer_question


def run_chat(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    answer_fn: Callable[[str], str] = answer_question,
) -> int:
    while True:
        try:
            question = input_fn("Faça sua pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            output_fn("")
            return 0

        if not question:
            continue

        try:
            answer = answer_fn(question)
        except (
            ConfigurationError,
            GoogleGenerativeAIError,
            SQLAlchemyError,
            ValueError,
        ) as error:
            print(f"Falha no chat: {error}", file=sys.stderr)
            return 1

        output_fn(f"PERGUNTA: {question}\nRESPOSTA: {answer}")


def main() -> int:
    return run_chat()


if __name__ == "__main__":
    raise SystemExit(main())
