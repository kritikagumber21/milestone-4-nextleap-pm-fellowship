"""Embedding utilities for the HDFC mutual fund facts RAG pipeline."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the canonical MiniLM model once per process."""
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts and return a list of 384-d vectors."""
    clean_texts = [text.strip() for text in texts if isinstance(text, str) and text.strip()]
    if not clean_texts:
        return []

    model = _get_model()
    embeddings = model.encode(clean_texts, show_progress_bar=False, convert_to_numpy=True)
    return [embedding.tolist() for embedding in embeddings]
