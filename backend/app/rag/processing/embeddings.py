"""
Text embedding utilities using ChromaDB's in-process ONNX all-MiniLM-L6-v2 model (384 dimensions).
Completely standalone — zero external Ollama server required.
"""
from typing import List
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

EMBEDDING_MODEL = "all-minilm"
EMBEDDING_DIMENSIONS = 384

# In-process singleton embedding function
_default_embedding_fn = DefaultEmbeddingFunction()


def embed_texts(texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """Generate 384-dimensional embedding vectors for text chunks in-process."""
    if not texts:
        return []

    all_embeddings: List[List[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        embeddings = _default_embedding_fn(batch)
        all_embeddings.extend([vec.tolist() for vec in embeddings])

    return all_embeddings


def embed_query(text: str) -> List[float]:
    """Generate a single 384-dimensional embedding vector for a search query."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Query text cannot be empty")
    return embed_texts([cleaned])[0]
