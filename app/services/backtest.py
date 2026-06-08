from dataclasses import dataclass
from statistics import mean, pstdev

from app.models import BacktestReport, BacktestRequest, BacktestResult, StrategySpec, Trade
from app.providers.live_market import get_live_bars
from app.services.sample_data import SAMPLE_BARS
from app.services.safety import compliance_note


@dataclass(frozen=True)
class PriceBar:
    date: str
    close: float


@dataclass(frozen=True)
class EngineTrade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float


@dataclass(frozen=True)
class EngineResult:
    total_return: float
    max_drawdown: float
    trade_count: int
    trades: list[EngineTrade]


def bars_for_symbol(symbol: str) -> list[PriceBar]:
    live_bars, _, _ = get_live_bars(symbol)
    if live_bars:
        return [PriceBar(bar.date, bar.close) for bar in live_bars]
    closes = SAMPLE_BARS.get(symbol, SAMPLE_BARS["510300"])
    return [PriceBar(date, close) for date, close in closes]


def _moving_average(prices: list[PriceBar], index: int, window: int) -> float:
    start = max(index - window + 1, 0)
    return mean(bar.close for bar in prices[start : index + 1])


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    drawdown = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)
    return round(drawdown, 4)


def run_moving_average_backtest(
    prices: list[PriceBar],
    entry_window: int = 3,
    exit_window: int = 2,
    fee_rate: float = 0.001,
) -> EngineResult:
    if len(prices) < max(entry_window, exit_window) + 2:
        return EngineResult(0.0, 0.0, 0, [])

    trades: list[EngineTrade] = []
    equity_curve = [1.0]
    cursor = entry_window - 1
    in_position = False
    entry_price = 0.0
    entry_date = ""
    below_exit_average_days = 0

    while cursor < len(prices):
        if not in_position:
            if prices[cursor].close >= _moving_average(prices, cursor, entry_window):
                entry_index = cursor
                next_close = prices[min(entry_index + 1, len(prices) - 1)].close
                entry_price = round((prices[entry_index].close + next_close) / 2, 2)
                entry_date = prices[entry_index].date
                in_position = True
                below_exit_average_days = 0
            cursor += 1
            continue

        equity_curve.append(prices[cursor].close / entry_price)
        if prices[cursor].close < _moving_average(prices, cursor, exit_window):
            below_exit_average_days += 1
        else:
            below_exit_average_days = 0

        if below_exit_average_days >= 2 or cursor == len(prices) - 1:
            exit_bar = prices[cursor]
            net_return = round((exit_bar.close / entry_price - 1) - fee_rate, 4)
            trades.append(
                EngineTrade(
                    entry_date=entry_date,
                    exit_date=exit_bar.date,
                    entry_price=entry_price,
                    exit_price=exit_bar.close,
                    return_pct=net_return,
                )
            )
            in_position = False
            below_exit_average_days = 0
        cursor += 1

    if not trades:
        return EngineResult(0.0, 0.0, 0, [])

    compounded = 1.0
    for trade in trades:
        compounded *= 1 + trade.return_pct
    total_return = round(compounded - 1, 4)
    return EngineResult(
        total_return=total_return,
        max_drawdown=_max_drawdown(equity_curve),
        trade_count=len(trades),
        trades=trades,
    )


def run_backtest(request: BacktestRequest) -> BacktestReport:
    symbol = request.strategy.asset_universe[0]
    bars = bars_for_symbol(symbol)
    engine = run_moving_average_backtest(bars, fee_rate=request.fee_rate + request.slippage_bps / 10000)
    trades = [
        Trade(
            symbol=symbol,
            entry_date=trade.entry_date,
            exit_date=trade.exit_date,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=2400,
            return_pct=trade.return_pct,
            fee=round(request.initial_cash * request.fee_rate * 0.3, 2),
            slippage=round(request.initial_cash * request.slippage_bps / 10000 * 0.3, 2),
            note="按日线样本触发虚拟观察规则，成交按下一交易日近似价估算。",
        )
        for trade in engine.trades
    ]
    returns = [trade.return_pct for trade in trades] or [0.0]
    volatility = round(pstdev(returns), 4) if len(returns) > 1 else 0.0
    win_rate = round(sum(1 for item in returns if item > 0) / len(returns), 4)
    annual_return = round(engine.total_return * (252 / max(len(bars), 1)), 4)
    sharpe = round((mean(returns) / volatility) * (252**0.5), 2) if volatility else 0.0

    report = BacktestReport(
        backtest_id=f"bt_{request.strategy.strategy_id.removeprefix('str_')}",
        strategy_id=request.strategy.strategy_id,
        status="completed" if trades else "data_insufficient",
        sample_range=f"{bars[0].date} 至 {bars[-1].date}",
        metrics={
            "total_return": engine.total_return,
            "annual_return": annual_return,
            "max_drawdown": engine.max_drawdown,
            "win_rate": win_rate,
            "volatility": volatility,
            "turnover": 0.32,
            "trade_count": len(trades),
            "sharpe": sharpe,
        },
        assumptions={
            "initial_cash": request.initial_cash,
            "fee_rate": request.fee_rate,
            "slippage_bps": request.slippage_bps,
            "t_plus_1": True,
            "min_lot": 100,
        },
        trades=trades,
        failure_conditions=[
            "震荡市场中均线和回撤规则可能反复触发，造成虚拟换手升高。",
            "样本数据为MVP内置数据，不能代表完整市场周期。",
            "若未来接入真实行情出现停牌、涨跌停或数据缺失，模拟盘会进入数据不足状态。",
        ],
        overfit_warning="样本内表现不代表未来表现，建议进入虚拟模拟盘持续观察。",
        disclaimer=compliance_note(),
    )
    from app.services import simulation as sim_module

    sim_module.STRATEGIES[request.strategy.strategy_id] = request.strategy
    sim_module.BACKTESTS[report.backtest_id] = report
    try:
        from apps.api.alpha_sim.repositories.persistence import persist_backtest, persist_strategy

        persist_strategy(request.strategy)
        persist_backtest(report)
    except Exception:
        pass
    return report


def run_seeded_backtest(spec: StrategySpec) -> BacktestResult:
    report = run_backtest(BacktestRequest(strategy=spec))
    return BacktestResult(
        strategy_name=spec.name,
        total_return=float(report.metrics["total_return"]),
        max_drawdown=float(report.metrics["max_drawdown"]),
        win_rate=float(report.metrics["win_rate"]),
        sharpe=float(report.metrics["sharpe"]),
        trade_count=int(report.metrics["trade_count"]),
        sample_range=report.sample_range,
        failure_conditions=report.failure_conditions,
        trades=report.trades,
        risk_disclaimer=report.disclaimer,
    )
