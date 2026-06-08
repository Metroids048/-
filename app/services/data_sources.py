from typing import Literal

import pandas as pd

from app.models import (
    AnnouncementsResponse,
    AssetOverview,
    AssetBarsResponse,
    AssetProfile,
    AssetSearchItem,
    AssetSearchResponse,
    DataSourcesResponse,
    FinancialSnapshot,
    FundRiskCard,
    FundRiskCardRequest,
    MarketBar,
)
from app.services.indicators import build_indicators
from app.providers.live_market import (
    get_live_announcements,
    get_live_bars,
    get_live_source_statuses,
    live_source_ref_for_profile,
)
from app.services.sample_data import (
    ASSET_META,
    ASSET_NAMES,
    get_financial_snapshot,
    source_ref,
)
from app.services.safety import compliance_note


ASSET_SEARCH_DISCLAIMER = (
    "标的搜索和概览仅用于投资想法复盘、行情背景查看和后续体检上下文，不构成投资建议。"
)


def _resample_bars(bars: list[MarketBar], interval: Literal["1d", "1w", "1m"]) -> list[MarketBar]:
    if interval == "1d" or not bars:
        return bars

    frame = pd.DataFrame(
        [
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]
    )
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date"]).sort_values("date")
    if frame.empty:
        return []

    rule = "W-FRI" if interval == "1w" else "ME"
    grouped = (
        frame.set_index("date")
        .resample(rule)
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )

    result: list[MarketBar] = []
    for _, row in grouped.iterrows():
        result.append(
            MarketBar(
                date=row["date"].strftime("%Y-%m-%d"),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(float(row["volume"])),
            )
        )
    return result


def list_data_sources() -> DataSourcesResponse:
    return DataSourcesResponse(items=get_live_source_statuses())


def build_asset_risk_card(symbol: str, name: str = "") -> FundRiskCard:
    symbol = symbol.strip().upper()
    asset_name = name or ASSET_NAMES.get(symbol, "观察标的")
    if symbol.startswith("159"):
        risk_level = "谨慎"
        style = "成长风格弹性较高，短期波动通常更明显。"
    elif symbol.startswith("512"):
        risk_level = "高风险"
        style = "行业主题集中度较高，容易受单一板块情绪影响。"
    elif symbol.startswith("518"):
        risk_level = "观察"
        style = "避险资产更多用于组合波动对冲，需要关注外部宏观扰动。"
    else:
        risk_level = "观察"
        style = "宽基资产更适合用趋势、回撤和定投纪律跟踪。"

    return FundRiskCard(
        symbol=symbol,
        name=asset_name,
        risk_level=risk_level,
        plain_summary=f"{asset_name}当前更适合放入观察列表，用规则判断风险变化。{style}",
        evidence=[
            "近20日趋势线是主要观察口径。",
            "波动率需要和60日窗口对比，避免被短线情绪带走。",
            "最大回撤比单日涨跌更适合衡量普通用户的承受压力。",
            "成交额和资金流只作为辅助证据，不能单独形成结论。",
        ],
        risk_counterpoints=[
            "如果缩量下行，趋势信号容易失真。",
            "如果行业权重过高，净值可能跟随板块剧烈波动。",
            "如果用户短期要用钱，任何波动资产都不适合重仓暴露。",
        ],
        action_boundary="这不是买卖建议，只是把风险证据翻译成更容易理解的观察卡。",
        content_cta="可加入观察列表，后续对比风险等级和模拟策略表现。",
        source=(
            live_source_ref_for_profile(symbol)
            if symbol in ASSET_META or symbol in SAMPLE_BARS
            else source_ref("暂无行情样本").model_copy(update={"data_time": None, "quality_status": "partial"})
        ),
    )


def build_fund_risk_card(request: FundRiskCardRequest) -> FundRiskCard:
    return build_asset_risk_card(request.symbol, request.name)


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def search_assets(query: str = "", limit: int = 10) -> AssetSearchResponse:
    normalized_query = _normalize_symbol(query)
    normalized_limit = max(1, min(limit, 20))
    registry = []
    for symbol, meta in ASSET_META.items():
        registry.append(
            {
                "symbol": symbol,
                "name": meta["name"],
                "asset_type": meta["asset_type"],
                "market": meta["market"],
                "exchange": meta["exchange"],
                "tags": meta["tags"],
                "status": "researchable",
            }
        )

    if normalized_query:
        registry = [
            item
            for item in registry
            if normalized_query in item["symbol"]
            or normalized_query.lower() in str(item["name"]).lower()
            or any(normalized_query.lower() in str(tag).lower() for tag in item["tags"])
        ]

    source = source_ref("内置标的检索样本")
    items = [
        AssetSearchItem(
            symbol=item["symbol"],
            name=item["name"],
            asset_type=item["asset_type"],
            market=item["market"],
            exchange=item["exchange"],
            tags=item["tags"],
            status=item["status"],
            source=source,
            disclaimer=ASSET_SEARCH_DISCLAIMER,
        )
        for item in registry[:normalized_limit]
    ]
    return AssetSearchResponse(query=query, items=items, disclaimer=ASSET_SEARCH_DISCLAIMER)


def get_asset_profile(symbol: str) -> AssetProfile:
    symbol = _normalize_symbol(symbol)
    meta = ASSET_META.get(
        symbol,
        {
            "name": ASSET_NAMES.get(symbol, "观察标的"),
            "asset_type": "UNKNOWN",
            "market": "CN_A",
            "exchange": "unknown",
            "currency": "CNY",
            "tags": ["样本外标的"],
            "summary": "当前只有样本数据能力，真实接入后会展示完整标的资料。",
        },
    )
    profile_source = (
        live_source_ref_for_profile(symbol)
        if symbol in ASSET_META or symbol in SAMPLE_BARS
        else source_ref("暂无行情样本").model_copy(update={"data_time": None, "quality_status": "partial"})
    )
    return AssetProfile(
        symbol=symbol,
        name=meta["name"],
        asset_type=meta["asset_type"],
        market=meta["market"],
        exchange=meta["exchange"],
        currency=meta["currency"],
        status="researchable" if symbol in ASSET_META else "sample_fallback",
        tags=meta["tags"],
        summary=meta["summary"],
        research_entrypoints=["kline", "risk_card", "ask_ai", "strategy_lab"],
        source=profile_source,
    )


def get_asset_bars(symbol: str, interval: Literal["1d", "1w", "1m"] = "1d", limit: int = 120) -> AssetBarsResponse:
    symbol = _normalize_symbol(symbol)
    normalized_limit = max(1, min(limit, 1000))
    bars, source, notice = get_live_bars(symbol)
    interval_bars = _resample_bars(bars, interval)
    if normalized_limit and len(interval_bars) > normalized_limit:
        interval_bars = interval_bars[-normalized_limit:]

    fallback_notice = None
    if notice:
        fallback_notice = f"{compliance_note()} {notice}"
    elif source.quality_status != "ok":
        fallback_notice = f"{compliance_note()} 数据质量状态：{source.quality_status}。"

    indicators = build_indicators(interval_bars) if interval_bars else None
    if interval_bars:
        source = source.model_copy(update={"data_time": interval_bars[-1].date})

    return AssetBarsResponse(
        symbol=symbol,
        interval=interval,
        bars=interval_bars,
        source=source,
        fallback_notice=fallback_notice,
        indicators=indicators,
    )


def build_asset_overview(symbol: str) -> AssetOverview:
    symbol = _normalize_symbol(symbol)
    profile = get_asset_profile(symbol)
    risk_card = build_asset_risk_card(symbol, profile.name)
    bars_response = None
    bars: list[MarketBar] = []
    if symbol in ASSET_META or symbol in SAMPLE_BARS:
        bars_response = get_asset_bars(symbol, interval="1d", limit=60)
        bars = bars_response.bars
    latest_price = bars[-1].close if bars else None
    change_pct = None
    if len(bars) >= 2 and bars[-2].close:
        change_pct = round(bars[-1].close / bars[-2].close - 1, 6)

    source = (
        bars_response.source
        if bars_response
        else source_ref("暂无行情样本").model_copy(update={"data_time": None, "quality_status": "partial"})
    )
    quality_status = source.quality_status if bars_response else "partial"
    data_time = source.data_time if bars_response else None
    fallback_notice = bars_response.fallback_notice if bars_response else None
    if not bars:
        fallback_notice = f"{compliance_note()} 暂无足够行情样本，只展示标的背景和数据状态。"

    return AssetOverview(
        symbol=profile.symbol,
        name=profile.name,
        asset_type=profile.asset_type,
        market=profile.market,
        latest_price=latest_price,
        change_pct=change_pct,
        data_time=data_time,
        source=source,
        quality_status=quality_status,
        risk_level=risk_card.risk_level,
        risk_tags=profile.tags,
        suggested_next_steps=[
            "把代码和你的想法一起生成体检卡",
            "先查看数据来源和更新时间",
            "只把样本回放当作复盘材料",
        ],
        disclaimer=ASSET_SEARCH_DISCLAIMER,
        fallback_notice=fallback_notice,
    )


def get_asset_financials(symbol: str) -> FinancialSnapshot:
    return get_financial_snapshot(symbol)


def get_asset_announcements(symbol: str) -> AnnouncementsResponse:
    return AnnouncementsResponse(
        symbol=symbol,
        items=get_live_announcements(symbol),
        disclaimer=f"公告摘要用于投研解释和风险背景。{compliance_note()}",
    )
