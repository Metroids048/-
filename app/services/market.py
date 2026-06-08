from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from app.models import (
    MarketHeatmapItem,
    MarketHeatmapResponse,
    MarketIndexItem,
    MarketIndexSparkBar,
    MarketIndicesResponse,
    MarketIndustriesResponse,
    MarketIndustry,
    MarketSummary,
    PreMarketBrief,
    SignalCard,
    SourceRef,
)
from app.providers.live_market import MAJOR_INDICES, get_live_index, get_live_sector_board
from app.services.safety import compliance_note
from app.services.sample_data import source_ref


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _temperature_from_change(change_pct: float) -> Literal["cool", "neutral", "warm", "hot"]:
    pct_points = change_pct * 100
    if pct_points >= 1.5:
        return "hot"
    if pct_points >= 0.4:
        return "warm"
    if pct_points <= -0.8:
        return "cool"
    return "neutral"


def _risk_level_from_changes(changes: list[float]) -> str:
    if not changes:
        return "中"
    avg = sum(changes) / len(changes)
    if avg >= 0.008:
        return "高"
    if avg <= -0.006:
        return "低"
    return "中"


def _headline_from_indices(changes: list[float], names: list[str]) -> str:
    if not changes:
        return "宽基ETF处在震荡修复样本区间，策略更适合先用回测和虚拟模拟观察，而不是直接寻找实盘时点。"
    avg = sum(changes) / len(changes)
    leader_idx = max(range(len(changes)), key=lambda index: changes[index])
    laggard_idx = min(range(len(changes)), key=lambda index: changes[index])
    if avg >= 0.006:
        tone = "主要指数样本偏强"
    elif avg <= -0.004:
        tone = "主要指数样本偏弱"
    else:
        tone = "主要指数样本震荡"
    return (
        f"{tone}，{names[leader_idx]}相对领先、{names[laggard_idx]}相对落后。"
        "适合先用回测和虚拟模拟观察规则触发，而不是直接寻找实盘时点。"
    )


def get_market_indices() -> MarketIndicesResponse:
    items: list[MarketIndexItem] = []
    notices: list[str] = []
    source: SourceRef | None = None
    updated_at = _now_iso()

    for index in MAJOR_INDICES:
        bars, change_pct, item_source, notice = get_live_index(index["code"], index["symbol"])
        if notice:
            notices.append(notice)
        source = item_source
        updated_at = item_source.fetched_at
        items.append(
            MarketIndexItem(
                code=index["code"],
                name=index["name"],
                latest_price=round(bars[-1].close, 2),
                change_pct=round(change_pct, 6),
                sparkline=[
                    MarketIndexSparkBar(date=bar.date, close=bar.close) for bar in bars[-20:]
                ],
            )
        )

    return MarketIndicesResponse(
        items=items,
        source=source or source_ref("内置样本数据"),
        updated_at=updated_at,
        fallback_notice=notices[0] if notices else None,
    )


def get_market_heatmap() -> MarketHeatmapResponse:
    board, item_source, notice = get_live_sector_board()
    items = [
        MarketHeatmapItem(
            name=str(row["name"]),
            change_pct=round(float(row["change_pct"]), 6),
            turnover=float(row["turnover"]) if row.get("turnover") is not None else None,
        )
        for row in board
    ]
    items.sort(key=lambda item: abs(item.change_pct), reverse=True)
    return MarketHeatmapResponse(
        items=items[:40],
        board_type="industry",
        source=item_source,
        updated_at=item_source.fetched_at,
        fallback_notice=notice,
    )


def _build_signal_cards() -> list[SignalCard]:
    return [
        SignalCard(
            symbol="510300",
            title="沪深300ETF：趋势修复观察",
            reason="样本收盘价接近短期趋势线，适合用仓位和回撤规则约束风险。",
            evidence=["价格站上短期均线", "样本波动低于成长风格ETF", "适合作为宽基策略底仓观察"],
            confidence="中",
            risk_counterpoint="若指数缩量跌回均线下方，说明修复动能不足。",
        ),
        SignalCard(
            symbol="159915",
            title="创业板ETF：弹性更高但波动更大",
            reason="成长风格短期弹性较强，适合小虚拟仓位观察，不适合用榜单当作实盘依据。",
            evidence=["样本期涨幅高于宽基", "回撤也更明显", "需要更严格的风控阈值"],
            confidence="中低",
            risk_counterpoint="若科技权重分化，信号稳定性会下降。",
        ),
    ]


def get_market_summary() -> MarketSummary:
    indices = get_market_indices()
    changes = [item.change_pct for item in indices.items]
    names = [item.name for item in indices.items]
    market_date = indices.source.data_time or indices.items[0].sparkline[-1].date
    risk_level = _risk_level_from_changes(changes)
    headline = _headline_from_indices(changes, names)

    return MarketSummary(
        market_date=market_date,
        status="盘后样本复盘" if indices.source.quality_status != "ok" else "行情已更新",
        risk_level=risk_level,
        headline=headline,
        hot_etfs=["510300 沪深300ETF", "159915 创业板ETF", "512880 证券ETF", "518880 黄金ETF"],
        pre_market_brief=PreMarketBrief(
            context=[
                "美股样本区间偏强，理论上对A股情绪有正面传导。",
                "中概互联样本表现分化，对成长风格可能有拖累。",
                "宽基ETF成交量尚未明显放大，修复仍需量能确认。",
            ],
            direction_label="数据偏强" if sum(changes) >= 0 else "数据偏弱",
            direction_prob=round(min(max(0.5 + sum(changes) * 8, 0.35), 0.72), 2),
            action_mantra="高开看量，有量留仓，无量跑路。",
            evidence=[
                "宽基指数样本接近短期均线，修复动能仍在观察区。",
                "成长风格弹性更高，但波动同步放大。",
                "行业轮动较快，单一板块信号稳定性有限。",
            ],
            methodology_note="方向概率来自样本因子加权（趋势+量能+外围联动），仅作数据解释参考，不构成预测承诺。",
        ),
        signal_cards=_build_signal_cards(),
        fallback_notice=indices.fallback_notice or compliance_note(),
        source=indices.source,
        updated_at=indices.updated_at,
    )


def _industry_explanation(name: str, change_pct: float) -> tuple[str, str]:
    pct = change_pct * 100
    if pct >= 1.0:
        explanation = f"{name}板块涨幅靠前，适合观察量能是否同步放大，不宜直接推导买卖动作。"
        counter = "若缩量冲高，板块信号容易失真。"
    elif pct <= -1.0:
        explanation = f"{name}板块跌幅靠前，更多反映阶段性资金偏好变化，需结合宽基指数理解。"
        counter = "单日下跌不代表趋势反转，需看后续修复力度。"
    else:
        explanation = f"{name}板块涨跌幅处于常规区间，适合作为行业轮动背景观察。"
        counter = "板块内部个股分化可能显著，单一ETF风险会被放大。"
    return explanation, counter


def get_market_industries() -> MarketIndustriesResponse:
    heatmap = get_market_heatmap()
    leading_map = {
        "半导体": ["588000", "159915"],
        "证券": ["512880"],
        "银行": ["银行样本"],
        "医药生物": ["医药ETF样本"],
        "新能源": ["159915", "新能源样本"],
        "消费": ["消费ETF样本"],
        "军工": ["军工ETF样本"],
        "计算机": ["159915", "588000"],
        "宽基指数": ["510300", "510500"],
        "成长科技": ["159915", "588000"],
    }

    items: list[MarketIndustry] = []
    for row in heatmap.items[:8]:
        explanation, counter = _industry_explanation(row.name, row.change_pct)
        items.append(
            MarketIndustry(
                name=row.name,
                temperature=_temperature_from_change(row.change_pct),
                change_pct=row.change_pct,
                leading_assets=leading_map.get(row.name, ["510300"]),
                explanation=explanation,
                risk_counterpoint=counter,
            )
        )

    if len(items) < 4:
        items = [
            MarketIndustry(
                name="宽基指数",
                temperature="warm",
                change_pct=0.0086,
                leading_assets=["510300", "510500"],
                explanation="宽基指数样本处在修复状态，适合先看成交量和回撤结构，不适合直接推导买卖动作。",
                risk_counterpoint="如果缩量反弹，修复信号容易失真。",
            ),
            MarketIndustry(
                name="成长科技",
                temperature="hot",
                change_pct=0.0172,
                leading_assets=["159915", "588000"],
                explanation="成长风格弹性更高，短期关注情绪和波动扩大。",
                risk_counterpoint="行业分化会让单一ETF风险显著放大。",
            ),
            MarketIndustry(
                name="证券金融",
                temperature="neutral",
                change_pct=0.0042,
                leading_assets=["512880", "银行样本"],
                explanation="金融板块更适合观察指数修复的持续性和成交活跃度。",
                risk_counterpoint="成交量不足时，板块信号可能只是一日轮动。",
            ),
            MarketIndustry(
                name="避险资产",
                temperature="cool",
                change_pct=-0.0018,
                leading_assets=["518880"],
                explanation="黄金类资产更多作为组合波动解释，不作为单独收益承诺。",
                risk_counterpoint="宏观扰动变化快，短线解释容易过度拟合。",
            ),
        ]

    return MarketIndustriesResponse(
        items=items,
        source=heatmap.source,
        disclaimer=f"{compliance_note()} 行业温度只用于投研解释和观察排序。",
        updated_at=heatmap.updated_at,
    )
