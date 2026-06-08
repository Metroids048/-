from statistics import mean

from app.models import Citation, SourceRef
from app.providers.live_market import get_live_bars
from app.services.data_sources import build_asset_risk_card, get_asset_announcements, get_asset_financials, get_asset_profile
from app.services.safety import compliance_note
from pydantic import BaseModel, Field


class ResearchSection(BaseModel):
    title: str
    body: str
    evidence: list[str] = Field(default_factory=list)


class AssetResearchReport(BaseModel):
    symbol: str
    name: str
    generated_at: str
    trend_view: str
    key_levels: list[str]
    risk_points: list[str]
    model_signals: list[str]
    sections: list[ResearchSection]
    citations: list[Citation]
    disclaimer: str
    source: SourceRef


def _trend_from_bars(closes: list[float]) -> str:
    if len(closes) < 5:
        return "样本不足，只能做观察级描述。"
    short_ma = mean(closes[-5:])
    long_ma = mean(closes[-10:]) if len(closes) >= 10 else mean(closes)
    if short_ma > long_ma * 1.01:
        return "短期均线高于较长窗口，处于修复或偏强观察状态。"
    if short_ma < long_ma * 0.99:
        return "短期均线低于较长窗口，处于回撤或偏弱观察状态。"
    return "短期与较长窗口均线接近，处于震荡观察状态。"


def build_asset_research_report(symbol: str) -> AssetResearchReport:
    profile = get_asset_profile(symbol)
    bars, source, _ = get_live_bars(symbol)
    risk_card = build_asset_risk_card(symbol, profile.name)
    financials = get_asset_financials(symbol)
    announcements = get_asset_announcements(symbol)
    closes = [bar.close for bar in bars]
    recent_high = max(closes[-20:]) if closes else 0
    recent_low = min(closes[-20:]) if closes else 0
    last_close = closes[-1] if closes else 0
    drawdown = round(1 - last_close / recent_high, 4) if recent_high else 0

    sections = [
        ResearchSection(
            title="趋势观察",
            body=_trend_from_bars(closes),
            evidence=[f"最新收盘 {last_close}", f"20日高点 {recent_high}", f"20日低点 {recent_low}"],
        ),
        ResearchSection(
            title="关键位置",
            body="以下价位仅作结构观察，不构成买卖点。",
            evidence=[
                f"近20日高点：{recent_high}",
                f"近20日低点：{recent_low}",
                f"相对高点回撤：{drawdown:.2%}",
            ],
        ),
        ResearchSection(
            title="风险与反例",
            body=risk_card.plain_summary,
            evidence=risk_card.evidence[:4],
        ),
        ResearchSection(
            title="公告与财报背景",
            body=(
                f"最新财报期 {financials.latest_period}，质量状态 {financials.quality_status}。"
                f" 最新公告：{announcements.items[0].title if announcements.items else '暂无'}。"
            ),
            evidence=[item.title for item in announcements.items[:2]],
        ),
    ]

    return AssetResearchReport(
        symbol=symbol,
        name=profile.name,
        generated_at=source.fetched_at,
        trend_view=sections[0].body,
        key_levels=[f"阻力观察区 {recent_high}", f"支撑观察区 {recent_low}"],
        risk_points=risk_card.risk_counterpoints,
        model_signals=[
            "均线趋势观察",
            "20日回撤观察",
            "成交量变化观察",
            "风险卡证据聚合",
        ],
        sections=sections,
        citations=[
            Citation(source_type="market_bars", source_id=symbol, title=f"{profile.name} K线", url=f"/api/assets/{symbol}/bars"),
            Citation(source_type="risk_card", source_id=symbol, title=f"{profile.name} 风险卡", url=f"/api/assets/{symbol}/risk-card"),
            Citation(source_type="announcement", source_id=announcements.items[0].announcement_id if announcements.items else symbol, title="公告摘要"),
        ],
        disclaimer=f"本研报为规则聚合的投研观察材料，{compliance_note()}",
        source=source,
    )
