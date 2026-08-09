from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """
    Represents one chunk of a document.
    """

    chunk_id: int
    text: str
    start_position: int
    end_position: int


class DocumentChunker:
    """
    Splits extracted document text into manageable chunks.

    The chunker works on characters rather than tokens.
    This keeps the implementation simple and predictable
    for our current MVP.
    """

    def __init__(
        self,
        chunk_size: int = 4000,
        overlap: int = 400,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize extracted document text.
        """

        if not text:
            return ""

        lines = []

        for line in text.splitlines():
            cleaned_line = " ".join(
                line.split()
            )

            if cleaned_line:
                lines.append(cleaned_line)

        return "\n".join(lines)

    def chunk(
        self,
        text: str,
    ) -> list[DocumentChunk]:
        """
        Split document text into overlapping chunks.
        """

        cleaned_text = self.clean_text(text)

        if not cleaned_text:
            return []

        chunks: list[DocumentChunk] = []

        start = 0
        chunk_id = 1
        text_length = len(cleaned_text)

        while start < text_length:
            end = min(
                start + self.chunk_size,
                text_length,
            )

            chunk_text = cleaned_text[start:end].strip()

            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        start_position=start,
                        end_position=end,
                    )
                )

                chunk_id += 1

            if end >= text_length:
                break

            next_start = end - self.overlap

            if next_start <= start:
                raise RuntimeError(
                    "Chunker failed to make progress."
                )

            start = next_start

        return chunks


def chunk_document(
    text: str,
    chunk_size: int = 4000,
    overlap: int = 400,
) -> list[DocumentChunk]:
    """
    Convenience function for document chunking.
    """

    chunker = DocumentChunker(
        chunk_size=chunk_size,
        overlap=overlap,
    )

    return chunker.chunk(text)