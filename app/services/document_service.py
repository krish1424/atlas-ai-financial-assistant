from dataclasses import dataclass

from app.ai.agent import AtlasAgent
from app.tools.documents import (
    PDFExtractionError,
    extract_text_from_pdf,
)


@dataclass
class DocumentAnalysisResult:
    filename: str
    extracted_text: str
    answer: str


class DocumentAnalysisService:
    """
    Handles PDF extraction and AI-based document analysis.

    Responsibilities:
    1. Extract text from a PDF.
    2. Send the extracted content to Atlas.
    3. Return the AI-generated answer.
    """

    def __init__(self, agent: AtlasAgent | None = None):
        self.agent = agent or AtlasAgent()

    async def analyze_pdf(
        self,
        file_path: str,
        question: str,
    ) -> DocumentAnalysisResult:
        """
        Analyze a PDF and answer a question about it.
        """

        if not question or not question.strip():
            raise ValueError(
                "Document question cannot be empty."
            )

        question = question.strip()

        try:
            extracted_text = extract_text_from_pdf(
                file_path
            )

        except PDFExtractionError:
            raise

        document_prompt = (
            "The user has provided a financial document.\n\n"
            "Answer the user's question using the document "
            "content provided below.\n\n"
            "IMPORTANT RULES:\n"
            "- Use the document as the primary source.\n"
            "- Do not invent information that is not present "
            "in the document.\n"
            "- If the document does not contain enough "
            "information to answer the question, say so.\n"
            "- Clearly distinguish document facts from your "
            "analysis or interpretation.\n"
            "- Keep the answer concise and structured.\n\n"
            "DOCUMENT CONTENT:\n"
            "=================\n"
            f"{extracted_text}\n"
            "=================\n\n"
            "USER QUESTION:\n"
            f"{question}"
        )

        response = await self.agent.process(
            user_message=document_prompt,
            conversation_history=[],
        )

        filename = file_path.replace(
            "\\",
            "/",
        ).split("/")[-1]

        return DocumentAnalysisResult(
            filename=filename,
            extracted_text=extracted_text,
            answer=response.message,
        )