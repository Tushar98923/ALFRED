"""
ChromaDB vector store wrapper for the RAG pipeline.
Handles storage, retrieval, and management of document embeddings.
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb

from .chunker import Chunk
from .embeddings import embed_documents, embed_query

# Default paths — can be overridden via Django settings
DEFAULT_CHROMA_PATH = str(Path(__file__).resolve().parent.parent / 'chroma_data')
DEFAULT_COLLECTION = 'alfred_knowledge'


class VectorStore:
    """Persistent ChromaDB vector store for the ALFRED knowledge base."""

    def __init__(
        self,
        persist_path: str = DEFAULT_CHROMA_PATH,
        collection_name: str = DEFAULT_COLLECTION,
    ):
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, chunks: List[Chunk], batch_size: int = 50) -> int:
        """
        Embed and store a list of document chunks.
        Returns the number of chunks stored.
        """
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        embeddings = embed_documents(texts)

        stored = 0
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeds = embeddings[i:i + batch_size]

            ids = [
                f"{c.source}__chunk_{c.chunk_index}__{int(time.time())}"
                for c in batch_chunks
            ]
            documents = [c.text for c in batch_chunks]
            metadatas = [
                {
                    "source": c.source,
                    "chunk_index": c.chunk_index,
                    "ingested_at": int(time.time()),
                    **c.metadata,
                }
                for c in batch_chunks
            ]

            self._collection.add(
                ids=ids,
                embeddings=batch_embeds,
                documents=documents,
                metadatas=metadatas,
            )
            stored += len(batch_chunks)

        return stored

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for the most relevant chunks matching the query.

        Returns a list of dicts with keys: text, source, chunk_index, score
        """
        query_embedding = embed_query(query)

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        hits = []
        if results and results['documents'] and results['documents'][0]:
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0],
            ):
                hits.append({
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "chunk_index": meta.get("chunk_index", -1),
                    "score": 1.0 - dist,  # cosine distance → similarity
                })

        return hits

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def delete_by_source(self, source: str) -> None:
        """Delete all chunks from a specific source file."""
        self._collection.delete(where={"source": source})

    def count(self) -> int:
        """Return the total number of chunks in the collection."""
        return self._collection.count()

    def reset(self) -> None:
        """Delete the collection and recreate it."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------

_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Return the singleton VectorStore instance."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
