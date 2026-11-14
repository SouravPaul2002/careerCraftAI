import os
from pathlib import Path

import chromadb

from app.config.settings import settings

COLLECTION_NAME = "candidate_knowledge"


def _get_persist_dir() -> str:
    """Resolve and create the local folder where ChromaDB stores its files."""
    if settings.CHROMA_PERSIST_DIR.strip():
        persist_path = settings.CHROMA_PERSIST_DIR.strip()
    else:
        # <repo_root>/storage/chroma
        persist_path = str(Path(__file__).resolve().parents[3] / "storage" / "chroma")

    os.makedirs(persist_path, exist_ok=True)
    return persist_path


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client stored on disk."""
    return chromadb.PersistentClient(path=_get_persist_dir())


def get_collection():
    """Get or create the ChromaDB collection for candidate knowledge chunks."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _flatten_metadata(record: dict) -> dict[str, str | int | float | bool]:
    """Flatten record metadata into ChromaDB-safe primitive values (no dicts or None)."""
    flat: dict[str, str | int | float | bool] = {
        "user_id": int(record["user_id"]),
        "source_type": str(record["source_type"]),
        "external_id": str(record["external_id"]),
        "title": str(record["title"]),
        "chunk_index": int(record["chunk_index"]),
        "total_chunks": int(record["total_chunks"]),
        "content_hash": str(record["content_hash"]),
    }

    if record.get("url"):
        flat["url"] = str(record["url"])

    extra = record.get("metadata") or {}
    if isinstance(extra, dict):
        for key, value in extra.items():
            if isinstance(value, (str, int, float, bool)):
                flat[key] = value

    return flat


def upsert_document_chunks(
    user_id: int,
    chunk_records: list[dict],
    embeddings: list[list[float]],
) -> int:
    """Replace existing chunks for each document and store new embeddings in ChromaDB."""
    if not chunk_records:
        return 0

    if len(chunk_records) != len(embeddings):
        raise ValueError("chunk_records and embeddings must have the same length")

    collection = get_collection()

    # Remove old chunks for these documents so shrinking a file leaves no stale chunks
    external_ids = {str(record["external_id"]) for record in chunk_records}
    for ext_id in external_ids:
        delete_document_chunks(user_id=user_id, external_id=ext_id)

    ids = [
        f"{user_id}:{record['external_id']}:{record['chunk_index']}"
        for record in chunk_records
    ]
    documents = [str(record["content"]) for record in chunk_records]
    metadatas = [_flatten_metadata(record) for record in chunk_records]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(ids)


def delete_document_chunks(user_id: int, external_id: str) -> int:
    """Delete all stored chunks for a single document owned by the user."""
    collection = get_collection()
    existing = collection.get(
        where={"$and": [{"user_id": user_id}, {"external_id": external_id}]},
        include=[],
    )
    ids_to_delete = existing.get("ids") or []
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


def delete_user_chunks(user_id: int) -> int:
    """Delete every stored chunk belonging to a user."""
    collection = get_collection()
    existing = collection.get(where={"user_id": user_id}, include=[])
    ids_to_delete = existing.get("ids") or []
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


def get_stored_document_hashes(user_id: int) -> dict[str, str]:
    """Return {external_id: content_hash} from ChromaDB for incremental sync."""
    collection = get_collection()
    existing = collection.get(where={"user_id": user_id}, include=["metadatas"])
    hashes: dict[str, str] = {}

    for meta in existing.get("metadatas") or []:
        if not meta:
            continue
        ext_id = meta.get("external_id")
        content_hash = meta.get("content_hash")
        if isinstance(ext_id, str) and isinstance(content_hash, str):
            hashes[ext_id] = content_hash

    return hashes


def similarity_search(
    user_id: int,
    query_embedding: list[float],
    top_k: int = 5,
    where_filter: dict | None = None,
) -> list[dict]:
    """Find the most semantically similar chunks for this user in ChromaDB."""
    collection = get_collection()
    total_count = collection.count()
    if total_count == 0:
        return []

    if where_filter:
        conditions: list[dict] = [{"user_id": user_id}]
        if "$and" in where_filter and isinstance(where_filter["$and"], list):
            conditions.extend(where_filter["$and"])
        else:
            for key, value in where_filter.items():
                if key != "user_id":
                    conditions.append({key: value})
        chroma_where: dict = conditions[0] if len(conditions) == 1 else {"$and": conditions}
    else:
        chroma_where = {"user_id": user_id}

    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_count),
        where=chroma_where,
        include=["documents", "metadatas", "distances"],
    )

    ids = (raw.get("ids") or [[]])[0]
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]

    results: list[dict] = []
    for chunk_id, content, meta, dist in zip(ids, docs, metas, dists):
        meta_dict = dict(meta or {})
        similarity = round(1.0 - float(dist), 4)
        results.append(
            {
                "id": chunk_id,
                "chunk_id": chunk_id,
                "source_type": meta_dict.get("source_type"),
                "external_id": meta_dict.get("external_id"),
                "title": meta_dict.get("title"),
                "url": meta_dict.get("url"),
                "chunk_index": meta_dict.get("chunk_index"),
                "content": content,
                "metadata": meta_dict,
                "score": similarity,
            }
        )

    return results
