from app.models import AiAskRequest
from app.services.ai_ask import ask_alpha
from app.services.rag.pipeline import run_rag_query


def test_keyword_fallback_works_without_ollama(monkeypatch):
    monkeypatch.setattr("app.services.rag.pipeline.is_ollama_available", lambda: False)

    result = run_rag_query(
        question="回测和最大回撤分别是什么意思？",
        context={},
        entry_point="global",
    )

    assert result["mode"] == "retrieval_only"
    assert result["model_status"] == "offline"
    assert result["chunks"], "expected keyword retrieval fallback chunks"
    assert "暂无足够依据" not in result["answer"]


def test_high_risk_questions_are_still_blocked():
    response = ask_alpha(
        AiAskRequest(question="现在能买吗？要不要加仓？", entry_point="global", context={}),
    )

    assert response.risk_class == "blocked_investment_advice"
    assert "不能回答" in response.answer


def test_rag_answer_never_contains_scaffold_phrase(monkeypatch):
    monkeypatch.setattr("app.services.rag.pipeline.is_ollama_available", lambda: True)
    monkeypatch.setattr("app.services.rag.pipeline.llm_generate", lambda *args, **kwargs: "规则 RAG 骨架")
    monkeypatch.setattr(
        "app.services.rag.pipeline.retrieve_knowledge_chunks",
        lambda *args, **kwargs: [
            {
                "source_id": "kb_demo",
                "title": "回测不等于未来收益",
                "source_type": "internal_doc",
                "snippet": "回测只能说明历史样本中的表现，不代表未来收益。",
                "content": "回测只能说明历史样本中的表现，不代表未来收益。",
                "score": 0.9,
            }
        ],
    )
    monkeypatch.setattr("app.services.rag.pipeline.rerank_chunks", lambda _, chunks, top_k=5: chunks[:top_k])

    result = run_rag_query(
        question="为什么回测不等于未来收益？",
        context={},
        entry_point="knowledge_page",
    )

    assert "规则 RAG 骨架" not in result["answer"]
