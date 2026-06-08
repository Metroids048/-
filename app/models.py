from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["observe", "caution", "high_risk", "insufficient_data"]
QualityStatus = Literal["ok", "delayed", "partial", "unavailable", "conflict", "stale", "not_configured"]


class SourceRef(BaseModel):
    source_name: str
    source_url: str | None = None
    fetched_at: str
    data_time: str | None = None
    quality_status: QualityStatus = "ok"
    rights_status: str = "public_reference"


class SignalCard(BaseModel):
    symbol: str
    title: str
    reason: str
    evidence: list[str]
    confidence: str
    risk_counterpoint: str


class PreMarketBrief(BaseModel):
    context: list[str]
    direction_label: str
    direction_prob: float | None = None
    action_mantra: str
    evidence: list[str]
    methodology_note: str


class MarketSummary(BaseModel):
    market_date: str
    status: str
    risk_level: str
    headline: str
    hot_etfs: list[str]
    signal_cards: list[SignalCard]
    pre_market_brief: PreMarketBrief | None = None
    fallback_notice: str | None = None
    source: SourceRef | None = None
    updated_at: str | None = None


class AssetProfile(BaseModel):
    symbol: str
    name: str
    asset_type: str
    market: str
    exchange: str
    currency: str
    status: str
    tags: list[str]
    summary: str
    research_entrypoints: list[str]
    source: SourceRef


class MarketBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class AssetBarsResponse(BaseModel):
    symbol: str
    interval: str
    bars: list[MarketBar]
    source: SourceRef
    fallback_notice: str | None = None
    indicators: dict[str, Any] | None = None


class AssetSearchItem(BaseModel):
    symbol: str
    name: str
    asset_type: str
    market: str
    exchange: str
    tags: list[str]
    status: str
    source: SourceRef
    disclaimer: str


class AssetSearchResponse(BaseModel):
    query: str
    items: list[AssetSearchItem]
    disclaimer: str


class AssetOverview(BaseModel):
    symbol: str
    name: str
    asset_type: str
    market: str
    latest_price: float | None = None
    change_pct: float | None = None
    data_time: str | None = None
    source: SourceRef
    quality_status: QualityStatus
    risk_level: str
    risk_tags: list[str]
    suggested_next_steps: list[str]
    disclaimer: str
    fallback_notice: str | None = None


class MarketIndustry(BaseModel):
    name: str
    temperature: Literal["cool", "neutral", "warm", "hot"]
    change_pct: float
    leading_assets: list[str]
    explanation: str
    risk_counterpoint: str


class MarketIndustriesResponse(BaseModel):
    items: list[MarketIndustry]
    source: SourceRef
    disclaimer: str
    updated_at: str | None = None


class MarketIndexSparkBar(BaseModel):
    date: str
    close: float


class MarketIndexItem(BaseModel):
    code: str
    name: str
    latest_price: float
    change_pct: float
    sparkline: list[MarketIndexSparkBar]


class MarketIndicesResponse(BaseModel):
    items: list[MarketIndexItem]
    source: SourceRef
    updated_at: str
    fallback_notice: str | None = None


class MarketHeatmapItem(BaseModel):
    name: str
    change_pct: float
    turnover: float | None = None


class MarketHeatmapResponse(BaseModel):
    items: list[MarketHeatmapItem]
    board_type: str = "industry"
    source: SourceRef
    updated_at: str
    fallback_notice: str | None = None


class StrategyRule(BaseModel):
    type: str
    operator: str = ">="
    value: float | str
    description: str


class StrategyCompileRequest(BaseModel):
    prompt: str = Field(min_length=4)
    market: str = "CN_A_ETF"
    preferred_assets: list[str] = Field(default_factory=list)
    risk_level: str = "moderate"
    # Legacy fields kept so /api/strategy/compile remains compatible.
    risk_preference: str = "稳健"
    watchlist: list[str] = Field(default_factory=list)


class StrategySpec(BaseModel):
    strategy_id: str
    name: str
    source: str
    asset_universe: list[str]
    market: str = "CN_A_ETF"
    frequency: str = "1d"
    entry_rules: list[StrategyRule]
    exit_rules: list[StrategyRule]
    position_rule: dict[str, Any]
    risk_rule: dict[str, Any]
    constraints: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    explanation: str
    warnings: list[str]
    compliance_note: str


class Trade(BaseModel):
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: int = 0
    return_pct: float
    fee: float = 0.0
    slippage: float = 0.0
    note: str


class BacktestRequest(BaseModel):
    strategy: StrategySpec
    start_date: str = "2025-01-02"
    end_date: str = "2026-05-29"
    initial_cash: float = 100000
    fee_rate: float = 0.0003
    slippage_bps: int = 5


class BacktestReport(BaseModel):
    backtest_id: str
    strategy_id: str
    status: str
    sample_range: str
    metrics: dict[str, float | int]
    assumptions: dict[str, float | int | bool]
    trades: list[Trade]
    failure_conditions: list[str]
    overfit_warning: str
    disclaimer: str


class BacktestResult(BaseModel):
    """Legacy response model for older tests and endpoints."""

    strategy_name: str
    total_return: float
    max_drawdown: float
    win_rate: float
    sharpe: float
    trade_count: int
    sample_range: str
    failure_conditions: list[str]
    trades: list[Trade]
    risk_disclaimer: str


class PaperPosition(BaseModel):
    symbol: str
    quantity: int
    cost_price: float
    last_price: float
    market_value: float
    unrealized_return_pct: float


class EquityPoint(BaseModel):
    date: str
    equity: float
    drawdown: float


class PaperAccount(BaseModel):
    account_id: str
    strategy_id: str
    initial_cash: float
    cash: float
    equity: float
    positions: list[PaperPosition]
    trades: list[Trade]
    equity_curve: list[EquityPoint]
    disclaimer: str


class SimulationCreateRequest(BaseModel):
    strategy_id: str
    backtest_id: str
    initial_cash: float = 100000
    visibility: str = "public_delayed"


class SimulationRun(BaseModel):
    simulation_id: str
    strategy_id: str
    account_id: str
    status: str
    running_days: int
    last_updated_at: str
    risk_events: list[str]
    leaderboard_eligible: bool
    account: PaperAccount
    disclaimer: str


class SimulationSummary(BaseModel):
    simulation_id: str
    strategy_id: str
    name: str
    status: str
    paper_return: float
    max_drawdown: float
    running_days: int
    started_at: str


class SimulationListResponse(BaseModel):
    items: list[SimulationSummary]


class StrategyScore(BaseModel):
    strategy_id: str
    return_score: float
    drawdown_score: float
    stability_score: float
    turnover_penalty: float
    duration_score: float
    total_score: float


class LeaderboardItem(BaseModel):
    strategy_id: str
    simulation_id: str
    name: str
    strategy_type: str
    paper_return: float
    max_drawdown: float
    running_days: int
    total_score: float
    risk_level: RiskLevel
    source: str


class LeaderboardResponse(BaseModel):
    leaderboard_type: str
    title: str
    items: list[LeaderboardItem]
    disclaimer: str


class StrategyCard(BaseModel):
    strategy: StrategySpec
    backtest: BacktestReport
    simulation: SimulationRun | None = None
    alpha_diagnostics: dict[str, Any]
    risk_counterexamples: list[str]
    failure_conditions: list[str]
    disclaimer: str


class DataSourceStatus(BaseModel):
    source_name: str
    tier: str
    domains: list[str]
    status: QualityStatus
    last_synced_at: str | None
    rights_status: str
    display_policy: str


class DataSourcesResponse(BaseModel):
    items: list[DataSourceStatus]


class FundRiskCardRequest(BaseModel):
    symbol: str
    name: str = ""
    question: str = ""


class FundRiskCard(BaseModel):
    symbol: str
    name: str
    risk_level: str
    plain_summary: str
    evidence: list[str]
    risk_counterpoints: list[str]
    action_boundary: str
    content_cta: str
    source: SourceRef | None = None


class DataScoreDimension(BaseModel):
    name: str
    score: int
    status: Literal["healthy", "neutral", "caution"]
    note: str


class DataScoreCard(BaseModel):
    symbol: str
    name: str
    dimensions: list[DataScoreDimension]
    pattern_tags: list[str]
    composite_score: int
    plain_summary: str
    tracking_condition: str
    disclaimer: str


class WatchlistScanItem(BaseModel):
    symbol: str
    name: str
    bucket: Literal["needs_review", "neutral", "volatility_up"]
    composite_score: int
    summary: str
    pattern_tags: list[str]


class WatchlistScanResponse(BaseModel):
    portfolio_summary: str
    needs_review: list[WatchlistScanItem]
    neutral: list[WatchlistScanItem]
    volatility_up: list[WatchlistScanItem]
    disclaimer: str


class ReviewNarrativeSection(BaseModel):
    title: str
    body: str
    evidence: list[str]


class DailyReviewNarrative(BaseModel):
    market_date: str
    headline: str
    sections: list[ReviewNarrativeSection]
    tracking_condition: str
    disclaimer: str


class FinancialSnapshot(BaseModel):
    symbol: str
    market: str
    latest_period: str
    quality_status: QualityStatus
    source: SourceRef
    metrics: dict[str, float | int]
    explanation_boundary: str


class AnnouncementItem(BaseModel):
    announcement_id: str
    title: str
    announcement_type: str
    published_at: str
    source_name: str
    source_url: str
    summary: str
    risk_tags: list[str]
    rights_status: str


class AnnouncementsResponse(BaseModel):
    symbol: str
    items: list[AnnouncementItem]
    disclaimer: str


class AiAskRequest(BaseModel):
    question: str = Field(min_length=2)
    entry_point: str = "global"
    context: dict[str, str] = Field(default_factory=dict)
    stream: bool = False


class Citation(BaseModel):
    source_type: str
    source_id: str
    title: str
    url: str | None = None
    snippet: str | None = None


class SuggestedAction(BaseModel):
    type: str
    label: str


class AiAskResponse(BaseModel):
    answer_id: str
    risk_class: str
    answer: str
    citations: list[Citation]
    suggested_actions: list[SuggestedAction]
    disclaimer: str
    model_status: str | None = None
    mode: str | None = None


class ComplianceCheckRequest(BaseModel):
    scene: str = "general"
    text: str


class ComplianceCheckResponse(BaseModel):
    allowed: bool
    blocked_terms: list[str]
    replacement_guidance: str


class AlertCreate(BaseModel):
    symbol: str
    trigger: str
    channel: str


class AlertRecord(AlertCreate):
    id: int
    status: str
    compliance_note: str


class WatchlistCreate(BaseModel):
    symbol: str
    note: str = ""
    source: str = "asset_detail"


class WatchlistRecord(WatchlistCreate):
    id: int
    name: str
    status: str
    added_at: str
    compliance_note: str


class WatchlistResponse(BaseModel):
    items: list[WatchlistRecord]


class JournalCreate(BaseModel):
    symbol: str
    observation: str
    action: str
    outcome: str


class JournalRecord(JournalCreate):
    id: int
    created_at: str
    reflection_prompt: str


class RevenueTier(BaseModel):
    name: str
    price: str
    user_value: str


class ContentHome(BaseModel):
    product_name: str
    positioning: str
    hero_promise: str
    primary_cta: str
    compliance_boundary: list[str]


class IdeaDiagnoseRequest(BaseModel):
    idea: str = Field(min_length=2)
    market: str = "A股"
    risk_preference: str = "小白默认"
    symbol: str | None = None


class HistoricalReplay(BaseModel):
    similar_cases: int
    median_case: str
    worst_case: str
    max_drawdown: str


class IdeaDiagnosisCard(BaseModel):
    idea_id: str
    raw_idea: str
    symbol: str | None = None
    idea_type: str
    emotion_tag: str
    diagnosis_summary: str
    replay_type: Literal["demo_virtual_sample"] = "demo_virtual_sample"
    replay_note: str
    historical_replay: HistoricalReplay
    risk_flags: list[str]
    failure_cases: list[str]
    xiaobai_reminder: str
    diagnosis_basis: list[str] = Field(default_factory=list)
    diagnosis_lens: str = ""
    warning: str | None = None
    disclaimer: str


class TrendingIdeaItem(BaseModel):
    id: str
    title: str
    idea_type: str
    heat_score: int
    risk_score: int
    teaser: str


class TrendingIdeasResponse(BaseModel):
    items: list[TrendingIdeaItem]
    disclaimer: str


class ShareCardRequest(BaseModel):
    diagnosis_id: str | None = None
    platform: str = "xiaohongshu"
    diagnosis: dict | None = None


class ShortVideoScript(BaseModel):
    hook: str
    body: str
    ending: str


class ShareCardResponse(BaseModel):
    titles: list[str]
    body: str
    short_video_script: ShortVideoScript
    disclaimer: str


class StrategyValidationRequest(BaseModel):
    idea: str = Field(min_length=4)
    symbols: list[str] = Field(default_factory=list)


class StrategyValidationCard(BaseModel):
    card_title: str
    user_idea: str
    rules: list[str]
    backtest: dict[str, str | float | int]
    risk_counterexamples: list[str]
    user_next_step: str
    compliance_note: str


class KnowledgeLesson(BaseModel):
    term: str
    plain_explanation: str
    why_it_matters: str
    example: str


class KnowledgeBase(BaseModel):
    lessons: list[KnowledgeLesson]


class AlphaAssetSummary(BaseModel):
    available: bool
    scanned_factors: int = 0
    factor_families: int = 0
    duplicate_risk_count: int = 0
    overfit_alerts: int = 0
    strategy_card_candidates: int = 0
    backtest_ready_count: int = 0


class AlphaHealthAlert(BaseModel):
    level: Literal["info", "caution", "warning"]
    title: str
    detail: str


class AlphaFactorFamily(BaseModel):
    family: str
    pass_rate: float
    sample_count: int
    source: str = "unknown"


class AlphaFactory(BaseModel):
    public_positioning: str
    source_assets: dict[str, int | str]
    asset_summary: AlphaAssetSummary
    health_alerts: list[AlphaHealthAlert] = Field(default_factory=list)
    factor_families: list[AlphaFactorFamily] = Field(default_factory=list)
    content_ideas: list[dict[str, str]]
    internal_tools: list[str]


class BusinessValidation(BaseModel):
    north_star_metric: str
    mvp_metrics: dict[str, dict[str, str]]
    four_week_plan: list[dict[str, str]]
    pricing: list[RevenueTier]
    kill_criteria: list[str]
