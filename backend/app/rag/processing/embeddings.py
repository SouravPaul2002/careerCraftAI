import httpx

from app.config.settings import settings

EMBEDDING_MODEL = "all-minilm"
EMBEDDING_DIMENSIONS = 384


def embed_texts(texts: list[str], batch_size: int = 20) -> list[list[float]]:
    """Generate embedding vectors for a list of text chunks using local Ollama."""
    if not texts:
        return []

    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    all_embeddings: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = httpx.post(
            f"{base_url}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": batch,
            },
            timeout=60.0,
        )

        if response.status_code == 404:
            raise RuntimeError(
                f"Ollama embedding model '{EMBEDDING_MODEL}' not found. "
                f"Run: ollama pull {EMBEDDING_MODEL}"
            )

        response.raise_for_status()
        all_embeddings.extend(response.json()["embeddings"])

    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Generate a single embedding vector for a search query."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Query text cannot be empty")
    return embed_texts([cleaned])[0]