from app.models import BacktestRequest, StrategyCard
from app.services.alpha_adapter import alpha_diagnostics_for_prompt
from app.services.backtest import run_backtest
from app.services.safety import compliance_note
from app.services.simulation import BACKTESTS, SIMULATIONS, STRATEGIES, create_simulation_for_strategy, seed_demo_data
from app.services.strategy import StrategyCompileRequest, compile_strategy


def get_strategy_card(strategy_id: str) -> StrategyCard:
    seed_demo_data()
    strategy = STRATEGIES.get(strategy_id)
    if strategy is None:
        strategy = compile_strategy(
            StrategyCompileRequest(prompt="本地alpha启发的宽基ETF回撤分批观察", preferred_assets=["510300"])
        )
    backtest = next((item for item in BACKTESTS.values() if item.strategy_id == strategy.strategy_id), None)
    if backtest is None:
        backtest = run_backtest(BacktestRequest(strategy=strategy))
    simulation = next((item for item in SIMULATIONS.values() if item.strategy_id == strategy.strategy_id), None)
    if simulation is None:
        simulation = create_simulation_for_strategy(strategy, backtest)
    return StrategyCard(
        strategy=strategy,
        backtest=backtest,
        simulation=simulation,
        alpha_diagnostics=alpha_diagnostics_for_prompt(strategy.explanation),
        risk_counterexamples=[
            "样本期表现好不代表未来市场结构相同。",
            "若成交额萎缩或波动率放大，策略信号可能失真。",
            "若同类策略过多，可能存在因子拥挤和自相关风险。",
        ],
        failure_conditions=backtest.failure_conditions,
        disclaimer=compliance_note(),
    )
