import json
import math
import re
from typing import Any

from sqlmodel import select

from app.services.knowledge_search import search_knowledge
from app.services.rag.embedder import embed_texts
from apps.api.alpha_sim.database import get_session
from apps.api.alpha_sim.domain.models import KnowledgeDocument


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}", text.lower())


def _keyword_overlap_score(question: str, text: str) -> float:
    q_tokens = set(_tokenize(question))
    t_tokens = set(_tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = q_tokens & t_tokens
    return float(len(overlap)) / max(len(q_tokens), 1)


def _parse_embedding(raw_embedding: Any) -> list[float] | None:
    if raw_embedding is None:
        return None
    if isinstance(raw_embedding, str):
        try:
            raw_embedding = json.loads(raw_embedding)
        except json.JSONDecodeError:
            return None
    if not isinstance(raw_embedding, list):
        return None
    try:
        return [float(value) for value in raw_embedding]
    except (TypeError, ValueError):
        return None


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _keyword_chunks(question: str, top_k: int) -> list[dict[str, Any]]:
    lessons = search_knowledge(question, limit=max(top_k, 5))
    scored_chunks: list[tuple[float, dict[str, Any]]] = []
    for lesson in lessons:
        content = f"{lesson.plain_explanation} {lesson.why_it_matters} 示例：{lesson.example}".strip()
        score = _keyword_overlap_score(question, f"{lesson.term} {content}")
        if score <= 0:
            continue
        scored_chunks.append(
            (
                score + 0.1,
                {
                    "source_id": f"kb_{lesson.term}",
                    "document_id": f"kb_{lesson.term}",
                    "title": lesson.term,
                    "source_type": "knowledge_chunk",
                    "snippet": content[:240],
                    "content": content,
                    "score": score + 0.1,
                    "retrieved_by": "keyword",
                },
            )
        )
    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    if scored_chunks:
        return [chunk for _, chunk in scored_chunks[:top_k]]

    normalized_question = question.lower()
    domain_keywords = ("回测", "回撤", "模拟", "风险", "策略", "过拟合", "etf", "行业", "公告", "财报")
    if not any(keyword in normalized_question for keyword in domain_keywords):
        return []

    fallback_chunks: list[dict[str, Any]] = []
    for lesson in lessons[:top_k]:
        content = f"{lesson.plain_explanation} {lesson.why_it_matters} 示例：{lesson.example}".strip()
        fallback_chunks.append(
            {
                "source_id": f"kb_{lesson.term}",
                "document_id": f"kb_{lesson.term}",
                "title": lesson.term,
                "source_type": "knowledge_chunk",
                "snippet": content[:240],
                "content": content,
                "score": 0.05,
                "retrieved_by": "keyword",
            }
        )
    return fallback_chunks


def _vector_chunks(question: str, top_k: int) -> list[dict[str, Any]]:
    query_embedding_list = embed_texts([question])
    if not query_embedding_list:
        return []
    query_embedding = query_embedding_list[0]
    candidates: list[tuple[float, dict[str, Any]]] = []

    with get_session() as session:
        documents = list(session.exec(select(KnowledgeDocument)).all())

    for doc in documents:
        doc_embedding = _parse_embedding(doc.embedding)
        if doc_embedding is None:
            continue
        score = _cosine_similarity(query_embedding, doc_embedding)
        if score <= 0:
            continue
        candidates.append(
            (
                score,
                {
                    "source_id": doc.document_id,
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "snippet": doc.content[:240],
                    "content": doc.content,
                    "score": score,
                    "retrieved_by": "vector",
                },
            )
        )
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in candidates[:top_k]]


def retrieve_knowledge_chunks(question: str, top_k: int = 5) -> list[dict[str, Any]]:
    keyword_results = _keyword_chunks(question, top_k)
    vector_results = _vector_chunks(question, top_k)
    merged: dict[str, dict[str, Any]] = {}

    for chunk in keyword_results + vector_results:
        source_id = chunk["source_id"]
        existing = merged.get(source_id)
        if not existing:
            merged[source_id] = dict(chunk)
            continue
        existing["score"] = max(existing.get("score", 0.0), chunk.get("score", 0.0))
        existing["retrieved_by"] = "hybrid"

    ranked = sorted(merged.values(), key=lambda item: item.get("score", 0.0), reverse=True)
    return ranked[:top_k]
