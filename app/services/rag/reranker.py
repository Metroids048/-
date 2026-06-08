import os
from typing import Any

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")

_RERANKER = None
_RERANKER_READY = False
_RERANKER_FAILED = False


def _load_reranker():
    global _RERANKER, _RERANKER_READY, _RERANKER_FAILED
    if _RERANKER_READY:
        return _RERANKER
    if _RERANKER_FAILED:
        return None
    try:
        from FlagEmbedding import FlagReranker
    except ImportError:
        _RERANKER_FAILED = True
        return None

    try:
        _RERANKER = FlagReranker(RERANKER_MODEL, use_fp16=False)
        _RERANKER_READY = True
        return _RERANKER
    except Exception:
        _RERANKER_FAILED = True
        return None


def rerank_chunks(question: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    if not chunks:
        return []
    reranker = _load_reranker()
    if reranker is None:
        return chunks[:top_k]

    pairs = [[question, chunk.get("content") or chunk.get("snippet") or ""] for chunk in chunks]
    try:
        raw_scores = reranker.compute_score(pairs)
    except Exception:
        return chunks[:top_k]

    if isinstance(raw_scores, (int, float)):
        scores = [float(raw_scores)] * len(chunks)
    else:
        scores = [float(score) for score in raw_scores]

    ranked_pairs = sorted(zip(chunks, scores), key=lambda item: item[1], reverse=True)
    reranked: list[dict[str, Any]] = []
    for chunk, score in ranked_pairs[:top_k]:
        enriched = dict(chunk)
        enriched["rerank_score"] = score
        reranked.append(enriched)
    return reranked
