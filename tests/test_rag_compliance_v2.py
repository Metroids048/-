def test_ask_alpha_blocks_high_risk_questions_before_generation():
    from apps.api.alpha_sim.services.rag import AskAlphaService

    service = AskAlphaService()
    answer = service.ask("现在能买吗，跟哪个策略买？", entry_point="global", context={})

    assert answer.risk_class == "blocked_investment_advice"
    assert "不能回答" in answer.answer
    assert answer.citations[0]["source_type"] == "compliance_rule"
    assert answer.suggested_actions[0]["type"] == "create_strategy"
    assert service.question_logs[-1]["risk_class"] == "blocked_investment_advice"


def test_ask_alpha_explains_strategy_context_with_citations():
    from apps.api.alpha_sim.providers.registry import build_default_registry
    from apps.api.alpha_sim.services.rag import AskAlphaService
    from apps.api.alpha_sim.services.strategy_engine import BacktestEngine, PaperTradingEngine, StrategyCompiler

    registry = build_default_registry()
    strategy = StrategyCompiler().compile("沪深300回撤5%分批观察", ["510300"], "moderate")
    backtest = BacktestEngine(registry.market).run(strategy)
    simulation = PaperTradingEngine(registry.market).create_simulation(strategy, backtest)
    service = AskAlphaService(strategies={strategy.strategy_id: strategy}, backtests={strategy.strategy_id: backtest}, simulations={strategy.strategy_id: simulation})

    answer = service.ask("这个策略为什么回撤高？", entry_point="strategy_detail", context={"strategy_id": strategy.strategy_id})

    assert answer.risk_class == "strategy_explanation"
    assert "最大回撤" in answer.answer
    assert {citation["source_type"] for citation in answer.citations} >= {"strategy_spec", "backtest_report"}
    assert "不构成投资建议" in answer.disclaimer


def test_ask_alpha_returns_no_evidence_when_context_is_missing():
    from apps.api.alpha_sim.services.rag import AskAlphaService

    service = AskAlphaService()
    answer = service.ask("解释这个未知公告", entry_point="announcement", context={"announcement_id": "missing"})

    assert answer.risk_class == "no_grounded_evidence"
    assert "暂无足够依据" in answer.answer
    assert answer.citations == []

