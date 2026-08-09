import pytest

from app.tools.documents.chunker import (
    DocumentChunker,
    chunk_document,
)


def test_chunk_document_returns_multiple_chunks():
    text = "A" * 1000

    chunks = chunk_document(
        text,
        chunk_size=400,
        overlap=50,
    )

    assert len(chunks) > 1


def test_chunk_size_is_respected():
    text = "A" * 1000

    chunks = chunk_document(
        text,
        chunk_size=400,
        overlap=50,
    )

    for chunk in chunks:
        assert len(chunk.text) <= 400


def test_chunk_ids_are_sequential():
    text = "A" * 1000

    chunks = chunk_document(
        text,
        chunk_size=400,
        overlap=50,
    )

    assert [chunk.chunk_id for chunk in chunks] == list(
        range(1, len(chunks) + 1)
    )


def test_chunk_positions_are_valid():
    text = "A" * 1000

    chunks = chunk_document(
        text,
        chunk_size=400,
        overlap=50,
    )

    for chunk in chunks:
        assert 0 <= chunk.start_position < chunk.end_position
        assert chunk.end_position <= len(text)


def test_empty_document_returns_no_chunks():
    chunks = chunk_document(
        "",
        chunk_size=400,
        overlap=50,
    )

    assert chunks == []


def test_zero_chunk_size_raises_error():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=0,
            overlap=0,
        )


def test_negative_chunk_size_raises_error():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=-100,
            overlap=0,
        )


def test_negative_overlap_raises_error():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=400,
            overlap=-1,
        )


def test_overlap_equal_to_chunk_size_raises_error():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=400,
            overlap=400,
        )


def test_overlap_greater_than_chunk_size_raises_error():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=400,
            overlap=500,
        )