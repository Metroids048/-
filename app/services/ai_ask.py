from app.models import AiAskRequest, AiAskResponse, Citation, SuggestedAction
from app.services.rag.pipeline import run_rag_query
from app.services.safety import compliance_note, is_high_risk_question
from app.services.strategy_cards import get_strategy_card


AI_QUESTION_LOGS: list[dict[str, str]] = []


def _log_question(request: AiAskRequest, risk_class: str) -> None:
    AI_QUESTION_LOGS.append(
        {
            "question": request.question,
            "entry_point": request.entry_point,
            "risk_class": risk_class,
            "context": str(request.context),
        }
    )


def ask_alpha(request: AiAskRequest) -> AiAskResponse:
    if is_high_risk_question(request.question):
        _log_question(request, "blocked_investment_advice")
        return AiAskResponse(
            answer_id=f"ans_{len(AI_QUESTION_LOGS):03d}",
            risk_class="blocked_investment_advice",
            answer=(
                "我不能回答现在是否买入、卖出、加仓、清仓、跟随哪个策略或目标价是多少。"
                "可以帮你解释风险证据、把想法转成可回测规则，或查看虚拟模拟表现。"
            ),
            citations=[
                Citation(
                    source_type="compliance_rule",
                    source_id="cr_no_advice_001",
                    title="非投资建议边界",
                    url="/api/compliance/check",
                )
            ],
            suggested_actions=[
                SuggestedAction(type="create_strategy", label="把想法转成模拟策略"),
                SuggestedAction(type="view_risk_card", label="查看风险卡"),
            ],
            disclaimer=compliance_note(),
            model_status="blocked",
            mode="retrieval_only",
        )

    strategy_id = request.context.get("strategy_id", "")
    if strategy_id or request.entry_point in {"strategy_detail", "backtest"}:
        card = get_strategy_card(strategy_id)
        max_drawdown = card.backtest.metrics["max_drawdown"]
        _log_question(request, "strategy_explanation")
        return AiAskResponse(
            answer_id=f"ans_{len(AI_QUESTION_LOGS):03d}",
            risk_class="strategy_explanation",
            answer=(
                f"这个策略的核心是{card.strategy.name}。当前样本回测最大回撤为{max_drawdown}，"
                f"模拟盘运行{card.simulation.running_days if card.simulation else 0}天。"
                "如果你关注回撤，重点看触发规则是否在震荡阶段反复进出，以及手续费和滑点是否压低表现。"
            ),
            citations=[
                Citation(source_type="strategy_spec", source_id=card.strategy.strategy_id, title=card.strategy.name),
                Citation(source_type="backtest_report", source_id=card.backtest.backtest_id, title="回测报告"),
            ],
            suggested_actions=[
                SuggestedAction(type="view_backtest", label="查看回测详情"),
                SuggestedAction(type="view_simulation", label="查看模拟盘表现"),
            ],
            disclaimer=compliance_note(),
            model_status=None,
            mode="strategy_card",
        )

    rag_result = run_rag_query(
        question=request.question,
        context=request.context,
        entry_point=request.entry_point,
    )
    chunks = rag_result.get("chunks") or []
    citations = [
        Citation(
            source_type=str(chunk.get("source_type", "knowledge_chunk")),
            source_id=str(chunk.get("source_id", chunk.get("document_id", "unknown"))),
            title=str(chunk.get("title", "知识片段")),
            url=chunk.get("source_url"),
            snippet=(chunk.get("snippet") or "")[:240],
        )
        for chunk in chunks
    ]
    risk_class = "knowledge_answer" if citations else "insufficient_evidence"
    _log_question(request, risk_class)
    return AiAskResponse(
        answer_id=f"ans_{len(AI_QUESTION_LOGS):03d}",
        risk_class=risk_class,
        answer=str(rag_result.get("answer", "")),
        citations=citations,
        suggested_actions=[
            SuggestedAction(type="view_knowledge", label="查看知识库"),
            SuggestedAction(type="create_strategy", label="创建模拟策略"),
        ],
        disclaimer=compliance_note(),
        model_status=rag_result.get("model_status"),
        mode=rag_result.get("mode"),
    )
