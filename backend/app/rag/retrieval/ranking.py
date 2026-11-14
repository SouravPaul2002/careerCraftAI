def rank_and_filter_results(
    results: list[dict],
    min_score: float = 0.0,
    top_k: int = 5,
    max_per_source: int | None = None,
) -> list[dict]:
    """Filter low-similarity chunks, deduplicate, optionally diversify sources, and rank."""
    if not results:
        return []

    filtered = [r for r in results if float(r.get("score", 0.0)) >= min_score]
    filtered.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)

    ranked: list[dict] = []
    seen_keys: set[tuple] = set()
    counts_by_source: dict[str, int] = {}

    for item in filtered:
        ext_id = str(item.get("external_id") or "")
        chunk_idx = item.get("chunk_index")
        dedup_key = (ext_id, chunk_idx)

        if dedup_key in seen_keys:
            continue

        if max_per_source is not None and ext_id:
            if counts_by_source.get(ext_id, 0) >= max_per_source:
                continue
            counts_by_source[ext_id] = counts_by_source.get(ext_id, 0) + 1

        seen_keys.add(dedup_key)
        ranked.append(item)

        if len(ranked) >= top_k:
            break

    return ranked


def format_retrieval_context(results: list[dict]) -> str:
    """Format retrieved chunks with source references into a readable LLM context block."""
    if not results:
        return ""

    blocks: list[str] = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title") or "Untitled Source"
        source_type = item.get("source_type") or "unknown"
        url = item.get("url")
        header = f"[{idx}] {title} ({source_type})"
        if url:
            header += f" - {url}"
        blocks.append(f"{header}\n{item.get('content', '')}")

    return "\n\n---\n\n".join(blocks)

