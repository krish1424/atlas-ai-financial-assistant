from pathlib import Path

from app.tools.documents import (
    extract_text_from_pdf,
    get_pdf_page_count,
)


PDF_PATH = Path("uploads/test_financial_report.pdf")


def main() -> None:
    print("Testing PDF document extraction...")
    print()

    if not PDF_PATH.exists():
        print(
            f"PDF not found: {PDF_PATH}"
        )
        print()
        print(
            "Place a PDF named "
            "'test_financial_report.pdf' "
            "inside the uploads folder."
        )
        return

    try:
        page_count = get_pdf_page_count(PDF_PATH)

        print(
            f"Page count: {page_count}"
        )

        text = extract_text_from_pdf(PDF_PATH)

        print()
        print("PDF text extracted successfully.")
        print()
        print("=" * 60)
        print("EXTRACTED TEXT")
        print("=" * 60)

        print(text[:5000])

        if len(text) > 5000:
            print()
            print(
                f"... ({len(text) - 5000} more characters)"
            )

        print()
        print("=" * 60)
        print(
            f"Total extracted characters: {len(text)}"
        )

    except Exception as exc:
        print()
        print("PDF extraction failed.")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()