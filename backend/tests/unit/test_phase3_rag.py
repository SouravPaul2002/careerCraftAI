import pytest
from app.rag.processing.chunking import clean_text, chunk_text
from app.rag.processing.metadata import compute_content_hash, build_chunk_records
from app.rag.retrieval.filters import build_chroma_where
from app.rag.retrieval.ranking import rank_and_filter_results, format_retrieval_context


def test_clean_text():
    raw = "Hello\x00 world!\r\n\r\n\n\nThis is   a test.\r\n"
    cleaned = clean_text(raw)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "This is a test." in cleaned
    assert cleaned.startswith("Hello world!")


def test_chunk_text():
    text = "Paragraph one with some information.\n\nParagraph two with more details.\n\nParagraph three."
    chunks = chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) for c in chunks)


def test_compute_content_hash():
    text1 = "Candidate experience with Python."
    text2 = "Candidate experience with Python."
    text3 = "Candidate experience with Java."
    assert compute_content_hash(text1) == compute_content_hash(text2)
    assert compute_content_hash(text1) != compute_content_hash(text3)


def test_build_chunk_records():
    doc = {
        "external_id": "doc123",
        "source_type": "google_drive",
        "title": "Resume.pdf",
        "url": "https://drive.google.com/...",
        "document_type": "PDF",
        "text": "Senior Developer with experience in FastAPI and React.",
    }
    records = build_chunk_records(user_id=1, doc=doc, chunk_size=30, overlap=5)
    assert len(records) > 0
    assert records[0]["user_id"] == 1
    assert records[0]["external_id"] == "doc123"
    assert records[0]["source_type"] == "google_drive"
    assert "content_hash" in records[0]


def test_build_chroma_where():
    # User-isolated filter
    w = build_chroma_where(user_id=42)
    assert w == {"user_id": 42}

    # User-isolated with source filter
    w2 = build_chroma_where(user_id=42, source_type="github_repo")
    assert "$and" in w2
    assert {"user_id": 42} in w2["$and"]
    assert {"source_type": "github_repo"} in w2["$and"]


def test_rank_and_filter_results():
    candidates = [
        {"external_id": "repo1", "chunk_index": 0, "score": 0.9, "source_type": "github", "content": "Text 1"},
        {"external_id": "drive1", "chunk_index": 0, "score": 0.85, "source_type": "drive", "content": "Text 2"},
        {"external_id": "drive2", "chunk_index": 0, "score": 0.1, "source_type": "drive", "content": "Irrelevant"},
    ]
    ranked = rank_and_filter_results(candidates, min_score=0.4, top_k=2)
    assert len(ranked) == 2
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert all(r["score"] >= 0.4 for r in ranked)


def test_format_retrieval_context():
    chunks = [
        {
            "chunk_id": "1",
            "score": 0.88,
            "source_type": "google_drive",
            "title": "Resume.pdf",
            "url": None,
            "chunk_index": 0,
            "total_chunks": 1,
            "content": "5 years of Python experience.",
        }
    ]
    ctx = format_retrieval_context(chunks)
    assert "5 years of Python experience." in ctx
    assert "Resume.pdf" in ctx
    assert "[1] Resume.pdf (google_drive)" in ctx
