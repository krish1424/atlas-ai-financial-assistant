import asyncio

from app.services.document_service import (
    DocumentAnalysisService,
)
from app.tools.documents import chunk_document, extract_text_from_pdf


PDF_PATH = "uploads/test_financial_report.pdf"


async def main():
    print("Testing chunk-aware document analysis...")
    print()

    service = DocumentAnalysisService(
        chunk_size=400,
        chunk_overlap=50,
        max_chunks=3,
    )

    question = (
        "What is the outstanding debt and what "
        "does the report recommend about debt?"
    )

    extracted_text = extract_text_from_pdf(
        PDF_PATH
    )

    all_chunks = chunk_document(
        extracted_text,
        chunk_size=400,
        overlap=50,
    )

    print(
        f"Total document chunks: {len(all_chunks)}"
    )

    selected_chunks = service.select_relevant_chunks(
        chunks=all_chunks,
        question=question,
    )

    print(
        f"Selected relevant chunks: "
        f"{len(selected_chunks)}"
    )

    print()
    print("--- Selected Chunks ---")

    for chunk in selected_chunks:
        print(
            f"Chunk {chunk.chunk_id}: "
            f"{len(chunk.text)} characters"
        )

    print()

    result = await service.analyze_pdf(
        file_path=PDF_PATH,
        question=question,
    )

    print("--- Document ---")
    print(result.filename)

    print()
    print("--- Extracted Characters ---")
    print(len(result.extracted_text))

    print()
    print("--- Atlas Answer ---")
    print(result.answer)

    print()
    print(
        "Chunk-aware document analysis test completed successfully."
    )


if __name__ == "__main__":
    asyncio.run(main())