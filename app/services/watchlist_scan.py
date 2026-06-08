from app.models import DailyReviewNarrative, ReviewNarrativeSection, WatchlistScanItem, WatchlistScanResponse
from app.services.data_score import build_data_score_card
from app.services.market import get_market_summary
from app.services.safety import compliance_note
from app.services.watchlist import list_watchlist


def _classify_item(symbol: str, name: str) -> WatchlistScanItem:
    score_card = build_data_score_card(symbol, name)
    caution_patterns = {"量价背离", "放量缺资金"}
    has_caution = bool(caution_patterns.intersection(score_card.pattern_tags))
    rsi_hot = "情绪偏热" in score_card.pattern_tags

    if score_card.composite_score < 55 or has_caution:
        bucket = "needs_review"
        summary = score_card.plain_summary
    elif rsi_hot or score_card.composite_score >= 72:
        bucket = "volatility_up"
        summary = f"{name}数据波动或情绪指标抬升，建议优先核对风险卡与策略失效条件。"
    else:
        bucket = "neutral"
        summary = f"{name}数据维度整体中性，维持常规观察节奏。"

    return WatchlistScanItem(
        symbol=symbol,
        name=name,
        bucket=bucket,
        composite_score=score_card.composite_score,
        summary=summary,
        pattern_tags=score_card.pattern_tags,
    )


def scan_watchlist() -> WatchlistScanResponse:
    items = list_watchlist().items
    scanned = [_classify_item(item.symbol, item.name) for item in items]

    needs_review = [item for item in scanned if item.bucket == "needs_review"]
    neutral = [item for item in scanned if item.bucket == "neutral"]
    volatility_up = [item for item in scanned if item.bucket == "volatility_up"]

    if not scanned:
        portfolio_summary = "观察列表为空，可先加入标的再执行一键扫描。"
    elif needs_review:
        portfolio_summary = (
            f"共扫描 {len(scanned)} 只标的：{len(needs_review)} 只需优先复盘，"
            f"{len(volatility_up)} 只波动/情绪抬升，{len(neutral)} 只数据中性。"
        )
    else:
        portfolio_summary = (
            f"共扫描 {len(scanned)} 只标的：暂未出现显著数据恶化信号，"
            f"{len(volatility_up)} 只需关注波动放大，{len(neutral)} 只维持中性观察。"
        )

    return WatchlistScanResponse(
        portfolio_summary=portfolio_summary,
        needs_review=needs_review,
        neutral=neutral,
        volatility_up=volatility_up,
        disclaimer=f"扫描结果仅用于观察列表复盘，不构成买卖建议。{compliance_note()}",
    )


def build_daily_review_narrative() -> DailyReviewNarrative:
    market = get_market_summary()
    scan = scan_watchlist()
    brief = market.pre_market_brief

    sections: list[ReviewNarrativeSection] = [
        ReviewNarrativeSection(
            title="市场背景",
            body=market.headline,
            evidence=[market.status, f"风险温度：{market.risk_level}"],
        ),
    ]

    if brief:
        sections.append(
            ReviewNarrativeSection(
                title="盘前数据框架",
                body=f"{brief.direction_label}（样本概率 {int(brief.direction_prob * 100)}%）。口诀：{brief.action_mantra}",
                evidence=brief.evidence,
            )
        )

    if scan.needs_review:
        review_lines = [f"{item.symbol} {item.name}：{item.summary}" for item in scan.needs_review[:3]]
        sections.append(
            ReviewNarrativeSection(
                title="观察列表需复盘",
                body="以下标的在数据维度出现分歧或偏谨慎信号，建议对照风险卡与策略失效条件。",
                evidence=review_lines,
            )
        )

    if market.signal_cards:
        card = market.signal_cards[0]
        sections.append(
            ReviewNarrativeSection(
                title="样本信号跟踪",
                body=f"{card.title}：{card.reason}",
                evidence=card.evidence + [f"反例：{card.risk_counterpoint}"],
            )
        )

    tracking = brief.action_mantra if brief else "维持观察列表跟踪，优先用虚拟模拟验证规则而非冲动决策。"

    return DailyReviewNarrative(
        market_date=market.market_date,
        headline=f"{market.market_date} 盘后数据复盘",
        sections=sections,
        tracking_condition=tracking,
        disclaimer=f"复盘叙事由公开数据模板生成，不构成投资建议。{compliance_note()}",
    )
