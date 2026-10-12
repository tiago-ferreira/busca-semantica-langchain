import pytest
from langchain_core.documents import Document
from pypdf.errors import PdfReadError, PdfStreamError

from src import ingest


def test_splits_pdf_text_with_required_size_and_overlap(tmp_path, monkeypatch):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.touch()
    text = "a" * 2200

    class FakePDFLoader:
        def __init__(self, path):
            assert path == str(pdf_path)

        def load(self):
            return [Document(page_content=text, metadata={"page": 0})]

    monkeypatch.setattr(ingest, "PyPDFLoader", FakePDFLoader)

    chunks = ingest.load_and_split_pdf(pdf_path)

    assert [len(chunk.page_content) for chunk in chunks] == [1000, 1000, 500]
    assert chunks[0].page_content[-150:] == chunks[1].page_content[:150]
    assert chunks[1].page_content[-150:] == chunks[2].page_content[:150]


def test_missing_pdf_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="PDF file not found"):
        ingest.load_and_split_pdf(tmp_path / "missing.pdf")


def test_unreadable_pdf_error_is_not_swallowed(tmp_path):
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("not a PDF")

    with pytest.raises((PdfReadError, PdfStreamError)):
        ingest.load_and_split_pdf(pdf_path)


def test_pdf_without_extractable_text_is_rejected(tmp_path, monkeypatch):
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.touch()

    class EmptyPDFLoader:
        def __init__(self, path):
            pass

        def load(self):
            return [Document(page_content="   \n")]

    monkeypatch.setattr(ingest, "PyPDFLoader", EmptyPDFLoader)

    with pytest.raises(ValueError, match="No extractable text"):
        ingest.load_and_split_pdf(pdf_path)
