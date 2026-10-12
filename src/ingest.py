"""Load and split the root PDF for semantic indexing."""

import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai._common import GoogleGenerativeAIError
from sqlalchemy.exc import SQLAlchemyError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ConfigurationError, load_settings
from src.vector_store import create_embeddings, replace_vector_collection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = PROJECT_ROOT / "document.pdf"


def load_and_split_pdf(pdf_path: Path = PDF_PATH) -> list[Document]:
    """Load a PDF and split its text into overlapping 1,000-character chunks."""
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages = PyPDFLoader(str(pdf_path)).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(pages)
    if not chunks:
        raise ValueError(f"No extractable text found in PDF: {pdf_path}")
    return chunks


def main() -> int:
    try:
        settings = load_settings(PROJECT_ROOT / ".env")
        chunks = load_and_split_pdf()
        embeddings = create_embeddings(settings)
        replace_vector_collection(chunks, settings, embeddings)
    except (
        ConfigurationError,
        FileNotFoundError,
        GoogleGenerativeAIError,
        SQLAlchemyError,
        ValueError,
    ) as error:
        print(f"Falha na ingestão: {error}", file=sys.stderr)
        return 1

    print(f"Ingested {len(chunks)} chunks from {PDF_PATH.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
