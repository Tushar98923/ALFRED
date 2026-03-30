"""
Embedding wrapper for the RAG pipeline.
Uses Google's text-embedding-004 model via the google-generativeai SDK.
"""
import os
from typing import List

import google.generativeai as genai

# Configure once at import time
_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if _api_key:
    genai.configure(api_key=_api_key)

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIMENSION = 768


def embed_texts(
    texts: List[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = 50,
) -> List[List[float]]:
    """
    Embed a list of texts using Google's text-embedding-004 model.

    Args:
        texts: List of strings to embed.
        task_type: One of 'RETRIEVAL_DOCUMENT', 'RETRIEVAL_QUERY',
                   'SEMANTIC_SIMILARITY', 'CLASSIFICATION', 'CLUSTERING'.
        batch_size: Max texts per API call (API limit).

    Returns:
        List of embedding vectors (each a list of floats).
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=batch,
            task_type=task_type,
        )
        # result['embedding'] is a list of vectors when content is a list
        embeddings = result['embedding']
        if isinstance(embeddings[0], float):
            # Single text was passed, wrap it
            all_embeddings.append(embeddings)
        else:
            all_embeddings.extend(embeddings)

    return all_embeddings


def embed_query(text: str) -> List[float]:
    """Embed a single query text optimized for retrieval."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="RETRIEVAL_QUERY",
    )
    return result['embedding']


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed document chunks optimized for retrieval."""
    return embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
