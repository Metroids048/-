import json
from typing import Any

from app.services.llm_gateway import generate as llm_generate, is_ollama_available
from app.services.rag.reranker import rerank_chunks
from app.services.rag.retriever import retrieve_knowledge_chunks
from app.services.safety import is_high_risk_question

NO_EVIDENCE_ANSWER = "知识库和当前数据暂无足够依据，不能生成确定解释。已记录这个问题，后续可补充相关数据源或知识文档。"
HIGH_RISK_ANSWER = (
    "我不能回答“现在是否买入/卖出”这类问题，也不能推荐跟随某个策略。"
    "可以帮你做三件事：1）解释风险证据；2）把想法改写成可回测规则；3）查看历史回测和虚拟模拟表现。"
)


def _render_retrieval_summary(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return NO_EVIDENCE_ANSWER
    lines = ["基于当前知识片段，可先参考以下依据："]
    for index, chunk in enumerate(chunks[:3], start=1):
        title = chunk.get("title") or "知识片段"
        snippet = (chunk.get("snippet") or "").strip()
        lines.append(f"{index}. {title}：{snippet}")
    lines.append("这只是基于当前数据和知识库的解释，不构成投资建议。")
    return "\n".join(lines)


def _build_prompt(question: str, entry_point: str, context: dict[str, str], chunks: list[dict[str, Any]]) -> str:
    citation_lines = []
    for index, chunk in enumerate(chunks, start=1):
        citation_lines.append(
            f"[{index}] 标题：{chunk.get('title', '未知')} | 类型：{chunk.get('source_type', 'knowledge_chunk')} | 内容：{chunk.get('snippet', '')}"
        )
    cited_context = "\n".join(citation_lines)
    return (
        f"用户问题：{question}\n"
        f"入口：{entry_point}\n"
        f"页面上下文：{json.dumps(context, ensure_ascii=False)}\n"
        f"可用依据：\n{cited_context}\n\n"
        "请基于给定依据回答，并明确说明不构成投资建议。"
        "如果依据不足，请直接回答“暂无足够依据”。"
    )


def _sanitize_answer(text: str) -> str:
    cleaned = (text or "").replace("规则 RAG 骨架", "").strip()
    return cleaned


def run_rag_query(
    question: str,
    context: dict[str, str] | None,
    entry_point: str,
    top_k: int = 5,
    generate: bool = True,
) -> dict[str, Any]:
    safe_context = context or {}
    if is_high_risk_question(question):
        return {
            "chunks": [],
            "answer": HIGH_RISK_ANSWER,
            "model_status": "blocked",
            "mode": "retrieval_only",
            "risk_class": "blocked_investment_advice",
        }

    chunks = retrieve_knowledge_chunks(question, top_k=top_k)
    chunks = rerank_chunks(question, chunks, top_k=top_k)
    if not chunks:
        return {
            "chunks": [],
            "answer": NO_EVIDENCE_ANSWER,
            "model_status": "no_evidence",
            "mode": "retrieval_only",
        }

    if not generate:
        return {
            "chunks": chunks,
            "answer": _render_retrieval_summary(chunks),
            "model_status": "generation_disabled",
            "mode": "retrieval_only",
        }

    if not is_ollama_available():
        return {
            "chunks": chunks,
            "answer": _render_retrieval_summary(chunks),
            "model_status": "offline",
            "mode": "retrieval_only",
        }

    prompt = _build_prompt(question, entry_point, safe_context, chunks)
    system_prompt = (
        "你是Alpha模拟场助手。只能根据提供的依据回答，不得编造监管结论、行情和收益承诺，"
        "不能给出买卖建议。回答要简洁，并保持中文。"
    )
    try:
        generated = _sanitize_answer(llm_generate(prompt=prompt, system=system_prompt))
    except RuntimeError:
        return {
            "chunks": chunks,
            "answer": _render_retrieval_summary(chunks),
            "model_status": "offline",
            "mode": "retrieval_only",
        }

    if not generated:
        generated = _render_retrieval_summary(chunks)
        return {
            "chunks": chunks,
            "answer": generated,
            "model_status": "empty_output",
            "mode": "retrieval_only",
        }

    return {
        "chunks": chunks,
        "answer": generated,
        "model_status": "online",
        "mode": "full_rag",
    }
