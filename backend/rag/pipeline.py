"""
Main RAG pipeline orchestrator for ALFRED.
Ties together: file loading → chunking → embedding → vector storage → retrieval → generation.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import google.generativeai as genai

from .loaders import load_file, SUPPORTED_EXTENSIONS
from .chunker import chunk_document
from .vector_store import get_vector_store

_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if _api_key:
    genai.configure(api_key=_api_key)


# ── Prompt template ─────────────────────────────────────────────────

RAG_PROMPT_TEMPLATE = """You are ALFRED, a knowledgeable AI assistant. Answer the user's question using ONLY the context provided below. If the context does not contain enough information to answer the question, say so honestly — do not make up information.

When referencing information, mention which source document it came from.

--- CONTEXT ---
{context}
--- END CONTEXT ---

User Question: {question}

Answer:"""

NO_CONTEXT_PROMPT = """You are ALFRED, a knowledgeable AI assistant. The user asked a question but no relevant documents were found in the knowledge base. Let them know that you don't have any relevant information in the knowledge base for their question, and suggest they upload relevant documents.

User Question: {question}

Answer:"""


# ── Ingestion ────────────────────────────────────────────────────────

def ingest_document(
    file_path: str,
    source_name: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """
    Full ingestion pipeline: load file → chunk → embed → store in vector DB.

    Args:
        file_path: Path to the file to ingest.
        source_name: Display name for the source (defaults to filename).
        chunk_size: Character count per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        Dict with 'source', 'chunk_count', 'status'.
    """
    path = Path(file_path)
    source = source_name or path.name

    # Validate extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {
            'source': source,
            'chunk_count': 0,
            'status': 'error',
            'error': f'Unsupported file type: {path.suffix}',
        }

    # Load
    text = load_file(file_path)
    if not text or not text.strip():
        return {
            'source': source,
            'chunk_count': 0,
            'status': 'error',
            'error': 'File is empty or could not be read.',
        }

    # Chunk
    chunks = chunk_document(text, source=source, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    if not chunks:
        return {
            'source': source,
            'chunk_count': 0,
            'status': 'error',
            'error': 'No chunks produced from the file.',
        }

    # Embed & store
    store = get_vector_store()
    stored = store.ingest(chunks)

    return {
        'source': source,
        'chunk_count': stored,
        'status': 'ready',
    }


# ── Query ────────────────────────────────────────────────────────────

def query_knowledge(
    question: str,
    top_k: int = 5,
    min_score: float = 0.3,
) -> Dict[str, Any]:
    """
    Full RAG query pipeline: embed query → search → augment prompt → generate.

    Args:
        question: The user's question.
        top_k: Number of chunks to retrieve.
        min_score: Minimum similarity score to include a chunk.

    Returns:
        Dict with 'answer', 'sources', 'mode'.
    """
    store = get_vector_store()

    # Retrieve relevant chunks
    hits = store.search(question, top_k=top_k)

    # Filter by minimum relevance score
    relevant = [h for h in hits if h['score'] >= min_score]

    if not relevant:
        # No relevant context found
        prompt = NO_CONTEXT_PROMPT.format(question=question)
        sources = []
    else:
        # Build context from retrieved chunks
        context_parts = []
        sources = []
        seen_sources = set()

        for i, hit in enumerate(relevant, 1):
            context_parts.append(
                f"[Source: {hit['source']}, Chunk {hit['chunk_index'] + 1}] "
                f"(Relevance: {hit['score']:.0%})\n{hit['text']}"
            )
            if hit['source'] not in seen_sources:
                sources.append({
                    'name': hit['source'],
                    'score': round(hit['score'], 3),
                })
                seen_sources.add(hit['source'])

        context = '\n\n'.join(context_parts)
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    # Generate response with Gemini
    try:
        from .model_resolver import get_model
        model = get_model()
        response = model.generate_content(prompt)
        answer = (response.text or '').strip()
    except Exception as e:
        answer = f"Error generating response: {str(e)}"

    return {
        'answer': answer,
        'sources': sources,
        'mode': 'knowledge',
        'chunks_retrieved': len(relevant),
    }


# ── Delete ───────────────────────────────────────────────────────────

def delete_document(source_name: str) -> None:
    """Remove all chunks for a document from the vector store."""
    store = get_vector_store()
    store.delete_by_source(source_name)


def get_knowledge_stats() -> Dict[str, Any]:
    """Get stats about the knowledge base."""
    store = get_vector_store()
    return {
        'total_chunks': store.count(),
    }
