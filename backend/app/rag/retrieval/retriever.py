from app.rag.processing.embeddings import embed_query
from app.rag.retrieval.filters import build_chroma_where, build_metadata_filter
from app.rag.retrieval.ranking import rank_and_filter_results
from app.rag.vector_store import get_collection, similarity_search


def retrieve_relevant_chunks(
    user_id: int,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    source_type: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    repo: str | None = None,
    external_id: str | None = None,
    max_per_source: int | None = None,
) -> list[dict]:
    """Semantic search over the user's ChromaDB chunks with optional metadata filters."""
    where_filter = build_metadata_filter(
        source_type=source_type,
        document_type=document_type,
        category=category,
        repo=repo,
        external_id=external_id,
    )

    query_embedding = embed_query(query)
    candidate_k = max(top_k, top_k * 2)

    raw_results = similarity_search(
        user_id=user_id,
        query_embedding=query_embedding,
        top_k=candidate_k,
        where_filter=where_filter,
    )

    return rank_and_filter_results(
        results=raw_results,
        min_score=min_score,
        top_k=top_k,
        max_per_source=max_per_source,
    )


def retrieve_by_metadata(
    user_id: int,
    source_type: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    repo: str | None = None,
    external_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Retrieve stored chunks purely by metadata filters (no embedding query needed)."""
    collection = get_collection()
    where = build_chroma_where(
        user_id=user_id,
        source_type=source_type,
        document_type=document_type,
        category=category,
        repo=repo,
        external_id=external_id,
    )

    raw = collection.get(
        where=where,
        limit=limit,
        include=["documents", "metadatas"],
    )

    ids = raw.get("ids") or []
    docs = raw.get("documents") or []
    metas = raw.get("metadatas") or []

    results: list[dict] = []
    for chunk_id, content, meta in zip(ids, docs, metas):
        meta_dict = dict(meta or {})
        results.append(
            {
                "id": chunk_id,
                "source_type": meta_dict.get("source_type"),
                "external_id": meta_dict.get("external_id"),
                "title": meta_dict.get("title"),
                "url": meta_dict.get("url"),
                "chunk_index": meta_dict.get("chunk_index", 0),
                "content": content,
                "metadata": meta_dict,
                "score": None,
            }
        )

    results.sort(key=lambda item: (str(item["external_id"] or ""), int(item["chunk_index"] or 0)))
    return results

