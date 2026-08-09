import re
from dataclasses import dataclass

from app.ai.agent import AtlasAgent
from app.tools.documents import (
    DocumentChunk,
    PDFExtractionError,
    chunk_document,
    extract_text_from_pdf,
)


@dataclass
class DocumentAnalysisResult:
    filename: str
    extracted_text: str
    selected_chunks: list[DocumentChunk]
    answer: str


class DocumentAnalysisService:
    """
    Handles PDF extraction, chunking, relevant-chunk selection,
    and AI-based document analysis.
    """

    def __init__(
        self,
        agent: AtlasAgent | None = None,
        chunk_size: int = 4000,
        chunk_overlap: int = 400,
        max_chunks: int = 5,
    ):
        self.agent = agent or AtlasAgent()

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """
        Convert text into normalized keyword tokens.

        Common stopwords are removed so generic words such as
        "the", "is", "what", and "about" do not artificially
        increase chunk relevance.
        """

        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "how",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "this",
            "to",
            "was",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "with",
        }

        tokens = set(
            re.findall(
                r"\b[a-zA-Z0-9]{2,}\b",
                text.lower(),
            )
        )

        return tokens - stopwords

    @classmethod
    def _score_chunk(
        cls,
        chunk: DocumentChunk,
        question_tokens: set[str],
    ) -> int:
        """
        Calculate a simple keyword relevance score.

        This is intentionally deterministic and free.
        We can replace it with semantic retrieval later
        if the project requires it.
        """

        if not question_tokens:
            return 0

        chunk_tokens = cls._tokenize(chunk.text)

        return len(
            question_tokens.intersection(
                chunk_tokens
            )
        )

    def select_relevant_chunks(
        self,
        chunks: list[DocumentChunk],
        question: str,
    ) -> list[DocumentChunk]:
        """
        Select the most relevant document chunks.

        Matching chunks are ranked by keyword relevance.

        If no chunk matches the question keywords,
        return the first few chunks so Gemini can still
        reason about the document.
        """

        if not chunks:
            return []

        question_tokens = self._tokenize(question)

        scored_chunks = [
            (
                self._score_chunk(
                    chunk,
                    question_tokens,
                ),
                chunk.chunk_id,
                chunk,
            )
            for chunk in chunks
        ]

        scored_chunks.sort(
            key=lambda item: (
                item[0],
                -item[1],
            ),
            reverse=True,
        )

        relevant = [
            item[2]
            for item in scored_chunks
            if item[0] > 0
        ]

        if not relevant:
            return chunks[: self.max_chunks]

        return relevant[: self.max_chunks]

    @staticmethod
    def _build_document_prompt(
        question: str,
        chunks: list[DocumentChunk],
    ) -> str:
        """
        Build a grounded prompt using only selected chunks.
        """

        context_parts = []

        for chunk in chunks:
            context_parts.append(
                f"--- Document Chunk {chunk.chunk_id} ---\n"
                f"{chunk.text}"
            )

        document_context = "\n\n".join(
            context_parts
        )

        return (
            "The user has provided a financial document.\n\n"
            "Answer the user's question using the relevant "
            "document sections below.\n\n"
            "IMPORTANT RULES:\n"
            "- Treat the document content as the primary source.\n"
            "- Do not invent facts that are not supported by "
            "the document.\n"
            "- If the provided document sections do not contain "
            "enough information, clearly say that the document "
            "does not provide enough information.\n"
            "- Distinguish document facts from your own analysis "
            "or interpretation.\n"
            "- Do not claim that you reviewed information that "
            "was not provided in these document sections.\n"
            "- Keep the answer concise and structured.\n\n"
            "RELEVANT DOCUMENT SECTIONS:\n"
            "==============================\n"
            f"{document_context}\n"
            "==============================\n\n"
            "USER QUESTION:\n"
            f"{question}"
        )

    async def analyze_pdf(
        self,
        file_path: str,
        question: str,
    ) -> DocumentAnalysisResult:
        """
        Extract, chunk, retrieve relevant sections,
        and analyze a PDF.
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

        chunks = chunk_document(
            extracted_text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )

        if not chunks:
            raise ValueError(
                "No usable document chunks were created."
            )

        selected_chunks = self.select_relevant_chunks(
            chunks=chunks,
            question=question,
        )

        if not selected_chunks:
            raise ValueError(
                "No relevant document sections were found."
            )

        document_prompt = self._build_document_prompt(
            question=question,
            chunks=selected_chunks,
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
            selected_chunks=selected_chunks,
            answer=response.message,
        )