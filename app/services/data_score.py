from __future__ import annotations

from typing import Literal

from app.models import DataScoreCard, DataScoreDimension, MarketBar
from app.services.data_sources import get_asset_announcements, get_asset_bars
from app.services.indicators import bars_to_frame, compute_rsi
from app.services.sample_data import ASSET_NAMES
from app.services.safety import compliance_note


def _status_from_score(score: int) -> Literal["healthy", "neutral", "caution"]:
    if score >= 70:
        return "healthy"
    if score >= 50:
        return "neutral"
    return "caution"


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _volume_dimension(bars: list[MarketBar]) -> tuple[DataScoreDimension, float]:
    frame = bars_to_frame(bars)
    if len(frame) < 5:
        return (
            DataScoreDimension(name="量能", score=50, status="neutral", note="样本不足，量能维度暂用中性分。"),
            1.0,
        )

    recent = frame["volume"].tail(5).mean()
    baseline = frame["volume"].tail(20).mean() or 1.0
    ratio = float(recent / baseline)
    if ratio >= 1.2:
        score = _clamp_score(55 + min(ratio - 1.0, 1.0) * 35)
        note = f"近5日量能约为20日均值的{ratio:.2f}倍，成交活跃度抬升。"
    elif ratio <= 0.85:
        score = _clamp_score(45 - (0.85 - ratio) * 40)
        note = f"近5日量能约为20日均值的{ratio:.2f}倍，成交偏淡。"
    else:
        score = 65
        note = f"近5日量能约为20日均值的{ratio:.2f}倍，处于常规区间。"
    return DataScoreDimension(name="量能", score=score, status=_status_from_score(score), note=note), ratio


def _capital_dimension(bars: list[MarketBar], volume_ratio: float) -> DataScoreDimension:
    frame = bars_to_frame(bars)
    if len(frame) < 6:
        return DataScoreDimension(name="资金", score=50, status="neutral", note="样本不足，资金维度暂用中性分。")

    ret_5d = float(frame["close"].iloc[-1] / frame["close"].iloc[-6] - 1)
    last_bar = frame.iloc[-1]
    intraday_weak = float(last_bar["close"]) < float(last_bar["open"])

    if ret_5d > 0.02 and volume_ratio < 0.95:
        score = 42
        note = "价格抬升但量能未同步放大，资金跟进意愿偏弱（量价背离代理指标）。"
    elif volume_ratio > 1.25 and intraday_weak:
        score = 38
        note = "放量但收盘偏弱，可能存在阶段性分歧（放量缺资金代理指标）。"
    elif ret_5d > 0 and volume_ratio >= 1.0:
        score = 72
        note = "价格与量能同步改善，资金行为与价格方向一致。"
    elif ret_5d < -0.02 and volume_ratio > 1.1:
        score = 48
        note = "下跌伴随放量，需区分恐慌释放与趋势延续。"
    else:
        score = 60
        note = "资金行为与价格暂未出现显著背离。"
    return DataScoreDimension(name="资金", score=score, status=_status_from_score(score), note=note)


def _sentiment_dimension(bars: list[MarketBar]) -> tuple[DataScoreDimension, float | None]:
    rsi_values = compute_rsi(bars)
    if not rsi_values or rsi_values[-1] is None:
        return DataScoreDimension(name="情绪", score=55, status="neutral", note="RSI样本不足，情绪维度暂用中性分。"), None

    rsi = float(rsi_values[-1])
    if rsi >= 75:
        score = 40
        note = f"RSI={rsi:.1f}，短线情绪偏热，波动放大风险上升。"
    elif rsi >= 65:
        score = 52
        note = f"RSI={rsi:.1f}，情绪偏强但未极端。"
    elif rsi <= 35:
        score = 58
        note = f"RSI={rsi:.1f}，情绪偏冷，需结合趋势判断是否过度悲观。"
    else:
        score = 68
        note = f"RSI={rsi:.1f}，情绪处于常规区间。"
    return DataScoreDimension(name="情绪", score=score, status=_status_from_score(score), note=note), rsi


def _news_dimension(symbol: str) -> DataScoreDimension:
    announcements = get_asset_announcements(symbol)
    count = len(announcements.items)
    risk_tags = {tag for item in announcements.items for tag in item.risk_tags}
    if count == 0:
        score = 62
        note = "近期公告样本较少，消息面维度信息有限。"
    elif risk_tags:
        score = 45
        note = f"近期待关注公告 {count} 条，含风险标签：{', '.join(sorted(risk_tags)[:3])}。"
    else:
        score = 70
        note = f"近期公告 {count} 条，暂未出现显著风险标签。"
    return DataScoreDimension(name="消息", score=score, status=_status_from_score(score), note=note)


def _pattern_tags(
    volume_ratio: float,
    ret_5d: float,
    rsi: float | None,
    capital_score: int,
) -> list[str]:
    tags: list[str] = []
    if ret_5d > 0.02 and volume_ratio < 0.95:
        tags.append("量价背离")
    if volume_ratio > 1.25 and capital_score < 50:
        tags.append("放量缺资金")
    if ret_5d > 0 and volume_ratio >= 1.05 and capital_score >= 65:
        tags.append("量价同步")
    if rsi is not None and rsi >= 70:
        tags.append("情绪偏热")
    return tags


def build_data_score_card(symbol: str, name: str = "") -> DataScoreCard:
    asset_name = name or ASSET_NAMES.get(symbol, "观察标的")
    bars_payload = get_asset_bars(symbol, interval="1d", limit=120)
    bars = bars_payload.bars

    volume_dim, volume_ratio = _volume_dimension(bars)
    capital_dim = _capital_dimension(bars, volume_ratio)
    sentiment_dim, rsi = _sentiment_dimension(bars)
    news_dim = _news_dimension(symbol)

    dimensions = [volume_dim, capital_dim, sentiment_dim, news_dim]
    composite = _clamp_score(sum(item.score for item in dimensions) / len(dimensions))

    frame = bars_to_frame(bars)
    ret_5d = float(frame["close"].iloc[-1] / frame["close"].iloc[-6] - 1) if len(frame) >= 6 else 0.0
    pattern_tags = _pattern_tags(volume_ratio, ret_5d, rsi, capital_dim.score)

    if composite >= 68:
        plain_summary = f"{asset_name}多维数据综合分 {composite}，各维度暂未出现显著恶化信号。"
    elif composite >= 50:
        plain_summary = f"{asset_name}多维数据综合分 {composite}，部分维度存在分歧，宜继续观察而非冲动决策。"
    else:
        plain_summary = f"{asset_name}多维数据综合分 {composite}，数据维度偏谨慎，需优先核对量能与资金一致性。"

    if "量价背离" in pattern_tags or "放量缺资金" in pattern_tags:
        tracking = "放量缺资金时耐心观望；量能与资金同步向好后再纳入策略观察。"
    elif "量价同步" in pattern_tags:
        tracking = "量价同步改善时可纳入规则回测，但仍需虚拟模拟验证。"
    else:
        tracking = "维持观察列表跟踪，结合风险卡与策略失效条件复盘。"

    return DataScoreCard(
        symbol=symbol,
        name=asset_name,
        dimensions=dimensions,
        pattern_tags=pattern_tags,
        composite_score=composite,
        plain_summary=plain_summary,
        tracking_condition=tracking,
        disclaimer=f"数据评分只描述公开数据状态，不构成买卖建议。{compliance_note()}",
    )
