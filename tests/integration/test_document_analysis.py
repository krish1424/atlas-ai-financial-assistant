import pytest

from app.services.document_service import (
    DocumentAnalysisService,
)
from app.tools.documents.chunker import DocumentChunk


class FakeAgentResponse:
    def __init__(self, message: str):
        self.message = message


class FakeAtlasAgent:
    def __init__(self):
        self.received_prompt = None

    async def process(
        self,
        user_message: str,
        conversation_history,
    ):
        self.received_prompt = user_message

        return FakeAgentResponse(
            "The document reports monthly income of 75,000 "
            "and monthly savings of 27,000."
        )


def test_document_analysis_builds_grounded_prompt():
    service = DocumentAnalysisService(
        agent=FakeAtlasAgent(),
        chunk_size=400,
        chunk_overlap=50,
        max_chunks=3,
    )

    chunks = [
        DocumentChunk(
            chunk_id=1,
            text=(
                "Monthly Income: 75,000\n"
                "Monthly Expenses: 48,000\n"
                "Monthly Savings: 27,000"
            ),
            start_position=0,
            end_position=75,
        ),
        DocumentChunk(
            chunk_id=2,
            text=(
                "Emergency Fund: 1,80,000\n"
                "Total Investments: 4,50,000"
            ),
            start_position=75,
            end_position=130,
        ),
    ]

    selected_chunks = service.select_relevant_chunks(
        chunks=chunks,
        question="What are the monthly savings?",
    )

    prompt = service._build_document_prompt(
        question="What are the monthly savings?",
        chunks=selected_chunks,
    )

    assert "What are the monthly savings?" in prompt
    assert "Monthly Savings: 27,000" in prompt
    assert "IMPORTANT RULES:" in prompt
    assert "Do not invent facts" in prompt


def test_document_prompt_contains_only_selected_chunks():
    service = DocumentAnalysisService(
        agent=FakeAtlasAgent(),
    )

    selected_chunks = [
        DocumentChunk(
            chunk_id=2,
            text="Monthly Savings: 27,000",
            start_position=0,
            end_position=23,
        ),
    ]

    prompt = service._build_document_prompt(
        question="What are the monthly savings?",
        chunks=selected_chunks,
    )

    assert "Monthly Savings: 27,000" in prompt
    assert "Monthly Income: 75,000" not in prompt


def test_document_analysis_rejects_empty_question():
    service = DocumentAnalysisService(
        agent=FakeAtlasAgent(),
    )

    with pytest.raises(
        ValueError,
        match="Document question cannot be empty",
    ):
        # We test validation directly because analyze_pdf()
        # is asynchronous and this unit-level integration test
        # doesn't need a real PDF or Gemini call.
        import asyncio

        asyncio.run(
            service.analyze_pdf(
                file_path="test_financial_report.pdf",
                question="",
            )
        )


@pytest.mark.anyio
async def test_fake_agent_returns_grounded_response():
    agent = FakeAtlasAgent()

    service = DocumentAnalysisService(
        agent=agent,
        max_chunks=3,
    )

    chunks = [
        DocumentChunk(
            chunk_id=1,
            text="Monthly Savings: 27,000",
            start_position=0,
            end_position=23,
        ),
    ]

    selected_chunks = service.select_relevant_chunks(
        chunks=chunks,
        question="What are the monthly savings?",
    )

    prompt = service._build_document_prompt(
        question="What are the monthly savings?",
        chunks=selected_chunks,
    )

    response = await agent.process(
        user_message=prompt,
        conversation_history=[],
    )

    assert response.message
    assert "27,000" in response.message
    assert agent.received_prompt == prompt