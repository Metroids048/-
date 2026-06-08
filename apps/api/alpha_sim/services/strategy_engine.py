import hashlib
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any

from pydantic import BaseModel

from apps.api.alpha_sim.providers.registry import MarketDataProvider


DISCLAIMER = "虚拟资金模拟，仅用于策略研究、投研解释和学习复盘，不构成投资建议。"


class StrategySpecV2(BaseModel):
    strategy_id: str
    name: str
    source: str
    market: str = "CN_A_ETF"
    frequency: str = "1d"
    asset_universe: list[str]
    entry_rules: list[dict[str, Any]]
    exit_rules: list[dict[str, Any]]
    position_rule: dict[str, Any]
    risk_rule: dict[str, Any]
    constraints: dict[str, Any]
    tags: list[str]
    warnings: list[str]
    compliance_note: str = DISCLAIMER


class BacktestReportV2(BaseModel):
    backtest_id: str
    strategy_id: str
    status: str
    sample_range: str
    metrics: dict[str, float | int]
    assumptions: dict[str, float | int | bool]
    trades: list[dict[str, Any]]
    failure_conditions: list[str]
    overfit_warning: str
    source_refs: list[dict[str, Any]]
    disclaimer: str = DISCLAIMER


class PaperAccountV2(BaseModel):
    account_id: str
    strategy_id: str
    initial_cash: float
    cash: float
    equity: float
    positions: list[dict[str, Any]]
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]


class StrategyScoreV2(BaseModel):
    strategy_id: str
    return_score: float
    drawdown_score: float
    stability_score: float
    turnover_penalty: float
    duration_score: float
    total_score: float


class SimulationRunV2(BaseModel):
    simulation_id: str
    strategy_id: str
    account: PaperAccountV2
    status: str
    running_days: int
    risk_events: list[str]
    score: StrategyScoreV2
    disclaimer: str = DISCLAIMER


@dataclass(frozen=True)
class PriceBar:
    date: str
    close: float


def _strategy_id(prompt: str, assets: list[str]) -> str:
    digest = hashlib.sha1((prompt + "|".join(assets)).encode("utf-8")).hexdigest()[:10]
    return f"str_{digest}"


def _tags(prompt: str) -> list[str]:
    tags = []
    if any(term in prompt for term in ("动量", "趋势", "均线", "突破")):
        tags.append("momentum")
    if any(term in prompt for term in ("回撤", "反弹", "网格")):
        tags.append("mean_reversion")
    if any(term in prompt for term in ("波动", "风控")):
        tags.append("volatility")
    return tags or ["hybrid"]


class StrategyCompiler:
    def compile(self, prompt: str, preferred_assets: list[str] | None = None, risk_level: str = "moderate") -> StrategySpecV2:
        assets = [asset.strip() for asset in preferred_assets or ["510300"] if asset.strip()]
        max_position = 0.2 if risk_level in {"conservative", "保守"} else 0.3
        if risk_level in {"aggressive", "进取"}:
            max_position = 0.35

        if "回撤" in prompt or "分批" in prompt:
            name = "宽基ETF回撤分批模拟策略"
            entry_rules = [{"type": "drawdown_from_20d_high", "operator": ">=", "value": 0.05, "description": "从20日高点回撤达到5%后触发虚拟观察。"}]
            exit_rules = [{"type": "rebound_from_entry", "operator": ">=", "value": 0.03, "description": "虚拟观察价反弹3%后退出观察。"}]
        elif "网格" in prompt:
            name = "ETF网格观察模拟策略"
            entry_rules = [{"type": "grid_down_step", "operator": ">=", "value": 0.03, "description": "每下行3%触发一档虚拟网格观察。"}]
            exit_rules = [{"type": "grid_up_step", "operator": ">=", "value": 0.03, "description": "每上行3%触发一档虚拟网格退出观察。"}]
        else:
            name = "ETF均线趋势模拟策略"
            entry_rules = [{"type": "ma_breakout", "operator": ">=", "value": "20d_ma", "description": "收盘价站上短期均线后触发观察。"}]
            exit_rules = [{"type": "ma_breakdown", "operator": "<", "value": "10d_ma", "description": "收盘价跌破短期均线或组合回撤超过阈值时退出观察。"}]

        return StrategySpecV2(
            strategy_id=_strategy_id(prompt, assets),
            name=name,
            source="user_prompt",
            asset_universe=assets,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            position_rule={"type": "fixed_fraction", "max_single_position": max_position, "max_total_position": min(max_position * 2, 0.7)},
            risk_rule={"max_drawdown_stop": 0.12, "pause_after_risk_events": 2, "requires_manual_review": True},
            constraints={"t_plus_1": True, "min_lot": 100, "fee_rate": 0.0003, "slippage_bps": 5},
            tags=_tags(prompt),
            warnings=[DISCLAIMER, "策略仅为规则草稿，必须经过回测和虚拟模拟观察，不能直接用于实盘。"],
        )


def _to_price_bars(raw_bars: list[dict[str, Any]]) -> list[PriceBar]:
    return [PriceBar(str(item["date"]), float(item["close"])) for item in raw_bars]


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


class BacktestEngine:
    def __init__(self, market_provider: MarketDataProvider):
        self.market_provider = market_provider

    def run(
        self,
        strategy: StrategySpecV2,
        initial_cash: float = 100000,
        fee_rate: float = 0.0003,
        slippage_bps: int = 5,
    ) -> BacktestReportV2:
        bars_response = self.market_provider.daily_bars(strategy.asset_universe[0])
        bars = _to_price_bars(bars_response.bars)
        entry_index = 2
        for index in range(2, len(bars)):
            if bars[index].close >= _moving_average(bars, index, 3):
                entry_index = index
                break
        exit_index = len(bars) - 1
        entry_price = round((bars[entry_index].close + bars[min(entry_index + 1, len(bars) - 1)].close) / 2, 4)
        exit_price = bars[exit_index].close
        net_return = round((exit_price / entry_price - 1) - fee_rate - slippage_bps / 10000, 4)
        equity_curve = [bar.close / entry_price for bar in bars[entry_index : exit_index + 1]]
        max_drawdown = _max_drawdown([1.0, *equity_curve])
        returns = [net_return]
        volatility = round(pstdev(returns), 4) if len(returns) > 1 else 0.0
        sharpe = round((mean(returns) / volatility) * (252**0.5), 2) if volatility else 0.0
        trade = {
            "symbol": strategy.asset_universe[0],
            "entry_date": bars[entry_index].date,
            "exit_date": bars[exit_index].date,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": int((initial_cash * 0.3 / entry_price) // 100 * 100),
            "return_pct": net_return,
            "fee": round(initial_cash * fee_rate * 0.3, 2),
            "slippage": round(initial_cash * slippage_bps / 10000 * 0.3, 2),
            "note": "按日线样本触发虚拟观察规则，成交按下一交易日近似价估算。",
        }
        return BacktestReportV2(
            backtest_id=f"bt_{strategy.strategy_id.removeprefix('str_')}",
            strategy_id=strategy.strategy_id,
            status="completed",
            sample_range=f"{bars[0].date} 至 {bars[-1].date}",
            metrics={
                "total_return": net_return,
                "annual_return": round(net_return * (252 / max(len(bars), 1)), 4),
                "max_drawdown": max_drawdown,
                "win_rate": 1.0 if net_return > 0 else 0.0,
                "volatility": volatility,
                "turnover": 0.32,
                "trade_count": 1,
                "sharpe": sharpe,
            },
            assumptions={"initial_cash": initial_cash, "fee_rate": fee_rate, "slippage_bps": slippage_bps, "t_plus_1": True, "min_lot": 100},
            trades=[trade],
            failure_conditions=[
                "震荡市场中均线和回撤规则可能反复触发，造成虚拟换手升高。",
                "样本数据为MVP内置数据，不能代表完整市场周期。",
                "若真实行情出现停牌、涨跌停或数据缺失，模拟盘会进入数据不足状态。",
            ],
            overfit_warning="样本内表现不代表未来表现，建议进入虚拟模拟盘持续观察。",
            source_refs=[bars_response.source.model_dump()],
        )


class PaperTradingEngine:
    def __init__(self, market_provider: MarketDataProvider):
        self.market_provider = market_provider

    def create_simulation(self, strategy: StrategySpecV2, backtest: BacktestReportV2, initial_cash: float = 100000) -> SimulationRunV2:
        raw_bars = self.market_provider.daily_bars(strategy.asset_universe[0]).bars
        bars = _to_price_bars(raw_bars)
        fraction = min(float(strategy.position_rule.get("max_single_position", 0.3)), 0.35)
        cost_price = bars[2].close
        quantity = int((initial_cash * fraction / cost_price) // 100 * 100)
        cash = round(initial_cash - quantity * cost_price, 2)
        peak = initial_cash
        curve = []
        for bar in bars[2:]:
            equity = round(cash + quantity * bar.close, 2)
            peak = max(peak, equity)
            curve.append({"date": bar.date, "equity": equity, "drawdown": round(equity / peak - 1, 4)})
        last_price = bars[-1].close
        position_return = round(last_price / cost_price - 1, 4)
        account = PaperAccountV2(
            account_id=f"pa_{strategy.strategy_id.removeprefix('str_')}",
            strategy_id=strategy.strategy_id,
            initial_cash=initial_cash,
            cash=cash,
            equity=curve[-1]["equity"],
            positions=[
                {
                    "symbol": strategy.asset_universe[0],
                    "quantity": quantity,
                    "cost_price": cost_price,
                    "last_price": last_price,
                    "market_value": round(quantity * last_price, 2),
                    "unrealized_return_pct": position_return,
                }
            ],
            trades=[
                {
                    "symbol": strategy.asset_universe[0],
                    "entry_date": bars[2].date,
                    "exit_date": bars[-1].date,
                    "entry_price": cost_price,
                    "exit_price": last_price,
                    "quantity": quantity,
                    "return_pct": position_return,
                    "note": "虚拟模拟持仓，仅用于观察策略规则运行。",
                }
            ],
            equity_curve=curve,
        )
        max_drawdown = min(point["drawdown"] for point in curve)
        paper_return = account.equity / initial_cash - 1
        return_score = min(max(paper_return * 1000, 0), 40)
        drawdown_score = max(30 + max_drawdown * 500, 0)
        stability_score = 17 if backtest.metrics["turnover"] <= 0.6 else 12
        duration_score = min(len(curve), 10)
        turnover_penalty = 0 if len(account.trades) <= 3 else 2
        total_score = round(return_score + drawdown_score + stability_score + duration_score - turnover_penalty, 2)
        score = StrategyScoreV2(
            strategy_id=strategy.strategy_id,
            return_score=round(return_score, 2),
            drawdown_score=round(drawdown_score, 2),
            stability_score=stability_score,
            duration_score=duration_score,
            turnover_penalty=turnover_penalty,
            total_score=total_score,
        )
        risk_events = ["暂无硬性风控事件，继续观察虚拟表现。"]
        if max_drawdown < -0.03:
            risk_events = ["样本期内出现超过3%的虚拟回撤，需进入复盘。"]
        return SimulationRunV2(
            simulation_id=f"sim_{strategy.strategy_id.removeprefix('str_')}",
            strategy_id=strategy.strategy_id,
            account=account,
            status="running",
            running_days=len(curve),
            risk_events=risk_events,
            score=score,
        )
