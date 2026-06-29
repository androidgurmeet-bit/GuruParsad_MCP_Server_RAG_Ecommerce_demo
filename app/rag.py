from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np


def create_index(embeddings: list[list[float]]) -> faiss.Index:
    """Create a simple FAISS L2 index for dense vectors."""
    if len(embeddings) == 0:
        raise ValueError("embeddings must not be empty")

    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.asarray(embeddings, dtype="float32"))
    return index


def retrieve_chunks(
    query: str,
    *,
    embed_model,
    index: faiss.Index,
    chunks: list[str],
    k: int = 5,
) -> list[str]:
    """Return the top-k most similar chunks for the query."""
    if not query.strip():
        return []

    query_vector = embed_model.encode([query])
    _, ids = index.search(np.asarray(query_vector, dtype="float32"), k=k)
    return [chunks[i] for i in ids[0] if 0 <= i < len(chunks)]


@dataclass(frozen=True)
class RAGResult:
    answer: str
    sources: list[str]