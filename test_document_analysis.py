import asyncio

from app.services.document_service import (
    DocumentAnalysisService,
)


PDF_PATH = "uploads/test_financial_report.pdf"


async def main():
    print("Testing document analysis...")

    service = DocumentAnalysisService()

    question = (
        "What is the overall financial position "
        "according to this report?"
    )

    result = await service.analyze_pdf(
        file_path=PDF_PATH,
        question=question,
    )

    print()
    print("--- Document ---")
    print(result.filename)

    print()
    print("--- Extracted Characters ---")
    print(len(result.extracted_text))

    print()
    print("--- Atlas Answer ---")
    print(result.answer)


if __name__ == "__main__":
    asyncio.run(main())