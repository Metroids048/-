from app.models import (
    BacktestReport,
    BacktestRequest,
    EquityPoint,
    LeaderboardItem,
    LeaderboardResponse,
    PaperAccount,
    PaperPosition,
    SimulationCreateRequest,
    SimulationListResponse,
    SimulationRun,
    SimulationSummary,
    StrategyScore,
    StrategySpec,
    Trade,
)
from app.services.backtest import bars_for_symbol, run_backtest
from app.services.safety import compliance_note
from app.services.strategy import StrategyCompileRequest, compile_strategy


SIMULATIONS: dict[str, SimulationRun] = {}
STRATEGIES: dict[str, StrategySpec] = {}
BACKTESTS: dict[str, BacktestReport] = {}


SEED_PROMPTS = [
    ("沪深300回撤5%分批观察，反弹后退出虚拟仓位", ["510300"], "moderate"),
    ("创业板ETF站上20日均线后做行业ETF动量模拟", ["159915"], "aggressive"),
    ("证券ETF使用低回撤红利防守思路做风控观察", ["512880"], "conservative"),
    ("黄金ETF和宽基ETF做避险轮动模拟策略", ["518880", "510300"], "moderate"),
]


def _equity_curve(symbol: str, initial_cash: float, position_fraction: float) -> tuple[list[EquityPoint], PaperPosition, float]:
    bars = bars_for_symbol(symbol)
    quantity = int((initial_cash * position_fraction / bars[2].close) // 100 * 100)
    cost_price = bars[2].close
    cash = round(initial_cash - quantity * cost_price, 2)
    peak = initial_cash
    points = []
    for bar in bars[2:]:
        equity = round(cash + quantity * bar.close, 2)
        peak = max(peak, equity)
        drawdown = round(equity / peak - 1, 4)
        points.append(EquityPoint(date=bar.date, equity=equity, drawdown=drawdown))
    last_price = bars[-1].close
    position = PaperPosition(
        symbol=symbol,
        quantity=quantity,
        cost_price=cost_price,
        last_price=last_price,
        market_value=round(quantity * last_price, 2),
        unrealized_return_pct=round(last_price / cost_price - 1, 4),
    )
    return points, position, cash


def create_simulation_for_strategy(
    strategy: StrategySpec,
    backtest: BacktestReport,
    request: SimulationCreateRequest | None = None,
) -> SimulationRun:
    initial_cash = request.initial_cash if request else 100000
    symbol = strategy.asset_universe[0]
    fraction = min(float(strategy.position_rule.get("max_single_position", 0.3)), 0.35)
    curve, position, cash = _equity_curve(symbol, initial_cash, fraction)
    account_id = f"pa_{strategy.strategy_id.removeprefix('str_')}"
    simulation_id = f"sim_{strategy.strategy_id.removeprefix('str_')}"
    trade = Trade(
        symbol=symbol,
        entry_date=curve[0].date,
        exit_date=curve[-1].date,
        entry_price=position.cost_price,
        exit_price=position.last_price,
        quantity=position.quantity,
        return_pct=position.unrealized_return_pct,
        fee=round(initial_cash * 0.0003 * fraction, 2),
        slippage=round(initial_cash * 0.0005 * fraction, 2),
        note="虚拟模拟持仓，仅用于观察策略规则在样本行情中的运行。",
    )
    account = PaperAccount(
        account_id=account_id,
        strategy_id=strategy.strategy_id,
        initial_cash=initial_cash,
        cash=cash,
        equity=curve[-1].equity,
        positions=[position],
        trades=[trade],
        equity_curve=curve,
        disclaimer=compliance_note(),
    )
    risk_events = []
    if min(point.drawdown for point in curve) < -0.03:
        risk_events.append("样本期内出现超过3%的虚拟回撤，需进入复盘。")
    if float(backtest.metrics["turnover"]) > 0.6:
        risk_events.append("回测换手偏高，真实交易成本可能侵蚀表现。")

    run = SimulationRun(
        simulation_id=simulation_id,
        strategy_id=strategy.strategy_id,
        account_id=account_id,
        status="running",
        running_days=len(curve),
        last_updated_at="2026-06-07T09:00:00+08:00",
        risk_events=risk_events or ["暂无硬性风控事件，继续观察虚拟表现。"],
        leaderboard_eligible=len(curve) >= 5,
        account=account,
        disclaimer=compliance_note(),
    )
    STRATEGIES[strategy.strategy_id] = strategy
    BACKTESTS[backtest.backtest_id] = backtest
    SIMULATIONS[simulation_id] = run
    try:
        from apps.api.alpha_sim.repositories.persistence import persist_simulation, persist_strategy

        persist_strategy(strategy)
        persist_simulation(run)
    except Exception:
        pass
    return run


def create_simulation(request: SimulationCreateRequest) -> SimulationRun:
    backtest = BACKTESTS.get(request.backtest_id)
    strategy = STRATEGIES.get(request.strategy_id)
    if strategy is None and backtest is not None:
        strategy = STRATEGIES.get(backtest.strategy_id)
    if strategy is None:
        strategy = compile_strategy(
            StrategyCompileRequest(prompt="沪深300回撤5%分批观察", preferred_assets=["510300"], risk_level="moderate")
        )
    if backtest is None:
        backtest = run_backtest(BacktestRequest(strategy=strategy))
    return create_simulation_for_strategy(strategy, backtest, request)


def get_simulation(simulation_id: str) -> SimulationRun:
    seed_demo_data()
    if simulation_id not in SIMULATIONS:
        first = next(iter(SIMULATIONS.values()))
        return first
    return SIMULATIONS[simulation_id]


def list_simulations() -> SimulationListResponse:
    seed_demo_data()
    items: list[SimulationSummary] = []
    ordered_runs = sorted(SIMULATIONS.values(), key=lambda run: run.running_days, reverse=True)
    for run in ordered_runs:
        if run.status != "running":
            continue
        strategy = STRATEGIES.get(run.strategy_id)
        paper_return = round(run.account.equity / run.account.initial_cash - 1, 4)
        max_drawdown = min(point.drawdown for point in run.account.equity_curve)
        started_day = run.account.equity_curve[0].date if run.account.equity_curve else run.last_updated_at
        started_at = started_day if "T" in started_day else f"{started_day}T00:00:00+08:00"
        items.append(
            SimulationSummary(
                simulation_id=run.simulation_id,
                strategy_id=run.strategy_id,
                name=strategy.name if strategy else run.strategy_id,
                status=run.status,
                paper_return=paper_return,
                max_drawdown=max_drawdown,
                running_days=run.running_days,
                started_at=started_at,
            )
        )
    return SimulationListResponse(items=items)


def score_simulation(run: SimulationRun) -> StrategyScore:
    paper_return = run.account.equity / run.account.initial_cash - 1
    max_drawdown = min(point.drawdown for point in run.account.equity_curve)
    return_score = min(max(paper_return * 1000, 0), 40)
    drawdown_score = max(30 + max_drawdown * 500, 0)
    stability_score = max(20 - len(run.risk_events) * 3, 5)
    duration_score = min(run.running_days, 10)
    turnover_penalty = 2 if len(run.account.trades) > 3 else 0
    total = round(return_score + drawdown_score + stability_score + duration_score - turnover_penalty, 2)
    return StrategyScore(
        strategy_id=run.strategy_id,
        return_score=round(return_score, 2),
        drawdown_score=round(drawdown_score, 2),
        stability_score=round(stability_score, 2),
        turnover_penalty=turnover_penalty,
        duration_score=duration_score,
        total_score=total,
    )


def seed_demo_data() -> None:
    if SIMULATIONS:
        return
    for prompt, assets, risk in SEED_PROMPTS:
        strategy = compile_strategy(StrategyCompileRequest(prompt=prompt, preferred_assets=assets, risk_level=risk))
        report = run_backtest(BacktestRequest(strategy=strategy))
        create_simulation_for_strategy(strategy, report)


def get_leaderboard(board_type: str = "stability") -> LeaderboardResponse:
    seed_demo_data()
    resolved_type = "long_run" if board_type == "longevity" else board_type
    runs = [run for run in SIMULATIONS.values() if run.leaderboard_eligible]

    def key_for(run: SimulationRun) -> float:
        score = score_simulation(run)
        if resolved_type == "performance":
            return run.account.equity / run.account.initial_cash - 1
        if resolved_type == "risk_control":
            return min(point.drawdown for point in run.account.equity_curve) * -1
        if resolved_type == "long_run":
            return run.running_days
        return score.total_score

    reverse = resolved_type != "risk_control"
    ordered = sorted(runs, key=key_for, reverse=reverse)
    title_map = {
        "performance": "模拟表现榜",
        "stability": "稳定性榜",
        "risk_control": "风控榜",
        "long_run": "长跑榜",
        "longevity": "长跑榜",
    }
    items = []
    for run in ordered:
        strategy = STRATEGIES[run.strategy_id]
        score = score_simulation(run)
        paper_return = round(run.account.equity / run.account.initial_cash - 1, 4)
        max_drawdown = min(point.drawdown for point in run.account.equity_curve)
        items.append(
            LeaderboardItem(
                strategy_id=run.strategy_id,
                simulation_id=run.simulation_id,
                name=strategy.name,
                strategy_type=" / ".join(strategy.tags),
                paper_return=paper_return,
                max_drawdown=max_drawdown,
                running_days=run.running_days,
                total_score=score.total_score,
                risk_level="observe" if max_drawdown > -0.03 else "caution",
                source=strategy.source,
            )
        )
    return LeaderboardResponse(
        leaderboard_type=board_type,
        title=title_map.get(board_type, title_map.get(resolved_type, "稳定性榜")),
        items=items,
        disclaimer="榜单仅展示虚拟资金模拟表现，不构成投资建议，也不是跟买依据。",
    )
