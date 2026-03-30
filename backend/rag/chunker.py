"""
Text chunker for the RAG pipeline.
Splits documents into overlapping chunks for embedding.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    """A single chunk of text with its metadata."""
    text: str
    source: str          # Original file name
    chunk_index: int     # Position within the document
    metadata: dict = field(default_factory=dict)


def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: List[str] | None = None,
) -> List[str]:
    """
    Recursively split text into chunks using a hierarchy of separators.
    Tries to split on paragraph boundaries first, then sentences, then words.
    """
    if separators is None:
        separators = ['\n\n', '\n', '. ', ' ', '']

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Try each separator in order of preference
    for sep in separators:
        if sep == '':
            # Last resort: hard character split
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start = end - chunk_overlap
            return [c for c in chunks if c.strip()]

        parts = text.split(sep)
        if len(parts) == 1:
            continue  # This separator doesn't exist in the text

        # Merge parts into chunks that respect the size limit
        chunks = []
        current = ''
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                # If a single part exceeds chunk_size, recursively split it
                if len(part) > chunk_size:
                    remaining_seps = separators[separators.index(sep) + 1:]
                    sub_chunks = split_text(part, chunk_size, chunk_overlap, remaining_seps)
                    chunks.extend(sub_chunks)
                    current = ''
                else:
                    current = part

        if current.strip():
            chunks.append(current.strip())

        if chunks:
            # Apply overlap: prepend tail of previous chunk to the next one
            if chunk_overlap > 0 and len(chunks) > 1:
                overlapped = [chunks[0]]
                for i in range(1, len(chunks)):
                    prev = chunks[i - 1]
                    overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
                    merged = overlap_text + ' ' + chunks[i]
                    overlapped.append(merged)
                return overlapped
            return chunks

    return [text] if text.strip() else []


def chunk_document(
    text: str,
    source: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Chunk]:
    """
    Split a document's text into Chunk objects with metadata.
    """
    raw_chunks = split_text(text, chunk_size, chunk_overlap)
    return [
        Chunk(text=c, source=source, chunk_index=i)
        for i, c in enumerate(raw_chunks)
    ]
