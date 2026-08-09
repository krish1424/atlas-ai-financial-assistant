from app.tools.documents import (
    DocumentChunker,
    extract_text_from_pdf,
)


PDF_PATH = "uploads/test_financial_report.pdf"


def main():
    print("Testing document chunking...")
    print()

    text = extract_text_from_pdf(
        PDF_PATH
    )

    print(
        f"Original characters: {len(text)}"
    )

    chunker = DocumentChunker(
        chunk_size=400,
        overlap=50,
    )

    chunks = chunker.chunk(text)

    print(
        f"Total chunks: {len(chunks)}"
    )

    print()

    for chunk in chunks:
        print("=" * 60)
        print(
            f"Chunk ID: {chunk.chunk_id}"
        )
        print(
            f"Characters: {len(chunk.text)}"
        )
        print(
            f"Position: "
            f"{chunk.start_position} → "
            f"{chunk.end_position}"
        )
        print()
        print(chunk.text)

    print()
    print("=" * 60)
    print("Document chunking test completed successfully.")


if __name__ == "__main__":
    main()