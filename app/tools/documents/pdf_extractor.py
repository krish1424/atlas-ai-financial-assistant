from pathlib import Path

from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Raised when PDF text extraction fails."""


def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text from all readable pages.

    Raises:
        FileNotFoundError:
            If the PDF does not exist.
        PDFExtractionError:
            If the PDF cannot be read or contains no extractable text.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    if not path.is_file():
        raise PDFExtractionError(
            f"Path is not a file: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(
            f"Expected a PDF file, got: {path.suffix}"
        )

    try:
        reader = PdfReader(str(path))

        extracted_pages: list[str] = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                raise PDFExtractionError(
                    f"Failed to extract text from page {page_number}."
                ) from exc

            text = text.strip()

            if text:
                extracted_pages.append(
                    f"--- Page {page_number} ---\n{text}"
                )

        if not extracted_pages:
            raise PDFExtractionError(
                "No extractable text was found in the PDF. "
                "The PDF may contain scanned images instead of text."
            )

        return "\n\n".join(extracted_pages)

    except PDFExtractionError:
        raise

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to read PDF: {path}"
        ) from exc


def get_pdf_page_count(file_path: str | Path) -> int:
    """
    Return the number of pages in a PDF.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    try:
        reader = PdfReader(str(path))
        return len(reader.pages)

    except Exception as exc:
        raise PDFExtractionError(
            f"Failed to read PDF: {path}"
        ) from exc