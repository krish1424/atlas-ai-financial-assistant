from app.services.document_service import (
    DocumentAnalysisService,
)
from app.tools.documents.chunker import DocumentChunk


def create_chunk(
    chunk_id: int,
    text: str,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        text=text,
        start_position=0,
        end_position=len(text),
    )


def test_tokenize_normalizes_text():
    tokens = DocumentAnalysisService._tokenize(
        "Revenue increased by 25% in 2026."
    )

    assert "revenue" in tokens
    assert "increased" in tokens
    assert "2026" in tokens
    assert "25" in tokens


def test_tokenize_ignores_single_character_tokens():
    tokens = DocumentAnalysisService._tokenize(
        "A B company revenue"
    )

    assert "a" not in tokens
    assert "b" not in tokens
    assert "company" in tokens
    assert "revenue" in tokens


def test_tokenize_removes_common_stopwords():
    tokens = DocumentAnalysisService._tokenize(
        "What is the revenue of the company?"
    )

    assert "what" not in tokens
    assert "is" not in tokens
    assert "the" not in tokens
    assert "of" not in tokens
    assert "revenue" in tokens
    assert "company" in tokens


def test_score_chunk_counts_matching_keywords():
    chunk = create_chunk(
        1,
        "IBM revenue increased significantly.",
    )

    question_tokens = {
        "ibm",
        "revenue",
        "increased",
    }

    score = DocumentAnalysisService._score_chunk(
        chunk,
        question_tokens,
    )

    assert score == 3


def test_score_chunk_returns_zero_when_no_match():
    chunk = create_chunk(
        1,
        "The company operates in the technology sector.",
    )

    question_tokens = {
        "revenue",
        "profit",
        "debt",
    }

    score = DocumentAnalysisService._score_chunk(
        chunk,
        question_tokens,
    )

    assert score == 0


def test_select_relevant_chunks_prioritizes_matching_chunks():
    service = DocumentAnalysisService(
        chunk_size=400,
        chunk_overlap=50,
        max_chunks=2,
    )

    chunks = [
        create_chunk(
            1,
            "The company operates globally.",
        ),
        create_chunk(
            2,
            "Revenue increased to 69 billion dollars.",
        ),
        create_chunk(
            3,
            "The company paid dividends to shareholders.",
        ),
    ]

    selected = service.select_relevant_chunks(
        chunks=chunks,
        question="What is the revenue?",
    )

    assert len(selected) == 1
    assert selected[0].chunk_id == 2


def test_select_relevant_chunks_returns_empty_for_empty_input():
    service = DocumentAnalysisService()

    selected = service.select_relevant_chunks(
        chunks=[],
        question="What is the revenue?",
    )

    assert selected == []


def test_select_relevant_chunks_returns_first_chunks_when_no_match():
    service = DocumentAnalysisService(
        max_chunks=2,
    )

    chunks = [
        create_chunk(
            1,
            "Company overview.",
        ),
        create_chunk(
            2,
            "Technology services.",
        ),
        create_chunk(
            3,
            "Employee information.",
        ),
    ]

    selected = service.select_relevant_chunks(
        chunks=chunks,
        question="What is the weather?",
    )

    assert len(selected) == 2
    assert [chunk.chunk_id for chunk in selected] == [1, 2]


def test_common_words_do_not_create_false_relevance():
    service = DocumentAnalysisService(
        max_chunks=2,
    )

    chunks = [
        create_chunk(
            1,
            "The company operates globally.",
        ),
        create_chunk(
            2,
            "Revenue increased significantly.",
        ),
        create_chunk(
            3,
            "The company paid dividends.",
        ),
    ]

    selected = service.select_relevant_chunks(
        chunks=chunks,
        question="What is the revenue?",
    )

    assert [chunk.chunk_id for chunk in selected] == [2]