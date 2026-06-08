def test_strategy_compiler_returns_structured_rules_without_trade_advice():
    from apps.api.alpha_sim.services.strategy_engine import StrategyCompiler

    compiler = StrategyCompiler()
    strategy = compiler.compile(
        prompt="沪深300回撤5%分批观察，反弹3%退出虚拟仓位",
        preferred_assets=["510300"],
        risk_level="moderate",
    )

    assert strategy.strategy_id.startswith("str_")
    assert strategy.name == "宽基ETF回撤分批模拟策略"
    assert strategy.entry_rules[0]["type"] == "drawdown_from_20d_high"
    assert strategy.constraints["t_plus_1"] is True
    assert "买入建议" not in str(strategy.model_dump())


def test_backtest_engine_uses_provider_bars_costs_and_failure_conditions():
    from apps.api.alpha_sim.providers.registry import build_default_registry
    from apps.api.alpha_sim.services.strategy_engine import BacktestEngine, StrategyCompiler

    registry = build_default_registry()
    strategy = StrategyCompiler().compile("沪深300站上20日均线后观察趋势", ["510300"], "moderate")
    report = BacktestEngine(registry.market).run(strategy, initial_cash=100000, fee_rate=0.0003, slippage_bps=5)

    assert report.status == "completed"
    assert report.strategy_id == strategy.strategy_id
    assert report.assumptions["t_plus_1"] is True
    assert report.metrics["trade_count"] >= 1
    assert report.metrics["max_drawdown"] <= 0
    assert len(report.failure_conditions) >= 3
    assert report.source_refs[0]["source_name"] == "AKShare"


def test_paper_trading_engine_creates_simulation_and_leaderboard_score():
    from apps.api.alpha_sim.providers.registry import build_default_registry
    from apps.api.alpha_sim.services.strategy_engine import BacktestEngine, PaperTradingEngine, StrategyCompiler

    registry = build_default_registry()
    strategy = StrategyCompiler().compile("创业板ETF站上20日均线后做行业ETF动量模拟", ["159915"], "aggressive")
    report = BacktestEngine(registry.market).run(strategy)
    simulation = PaperTradingEngine(registry.market).create_simulation(strategy, report)

    assert simulation.status == "running"
    assert simulation.account.initial_cash == 100000
    assert simulation.account.positions[0]["symbol"] == "159915"
    assert simulation.score.total_score > 0
    assert "虚拟资金模拟" in simulation.disclaimer

