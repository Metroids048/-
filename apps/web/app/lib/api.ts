export type SourceRef = {
  source_name: string;
  source_url?: string | null;
  fetched_at: string;
  data_time?: string | null;
  quality_status: string;
  rights_status: string;
};

export type MarketSummary = {
  market_date: string;
  status: string;
  risk_level: string;
  headline: string;
  hot_etfs: string[];
  signal_cards: {
    symbol: string;
    title: string;
    reason: string;
    evidence: string[];
    confidence: string;
    risk_counterpoint: string;
  }[];
  pre_market_brief?: PreMarketBrief | null;
  source?: SourceRef | null;
  updated_at?: string | null;
  fallback_notice?: string | null;
};

export type PreMarketBrief = {
  context: string[];
  direction_label: string;
  direction_prob?: number | null;
  action_mantra: string;
  evidence: string[];
  methodology_note: string;
};

export type MarketIndustry = {
  name: string;
  temperature: "cool" | "neutral" | "warm" | "hot";
  change_pct: number;
  leading_assets: string[];
  explanation: string;
  risk_counterpoint: string;
};

export type MarketIndexSparkBar = {
  date: string;
  close: number;
};

export type MarketIndexItem = {
  code: string;
  name: string;
  latest_price: number;
  change_pct: number;
  sparkline: MarketIndexSparkBar[];
};

export type MarketIndicesResponse = {
  items: MarketIndexItem[];
  source: SourceRef;
  updated_at: string;
  fallback_notice?: string | null;
};

export type MarketHeatmapItem = {
  name: string;
  change_pct: number;
  turnover?: number | null;
};

export type MarketHeatmapResponse = {
  items: MarketHeatmapItem[];
  board_type: string;
  source: SourceRef;
  updated_at: string;
  fallback_notice?: string | null;
};

export type MarketIndustriesResponse = {
  items: MarketIndustry[];
  source: SourceRef;
  disclaimer: string;
  updated_at?: string | null;
};

export type AssetProfile = {
  symbol: string;
  name: string;
  asset_type: string;
  market: string;
  exchange: string;
  currency: string;
  status: string;
  tags: string[];
  summary: string;
  research_entrypoints: string[];
  source: SourceRef;
};

export type MarketBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type BarIndicators = {
  ma?: {
    ma5?: Array<number | null>;
    ma10?: Array<number | null>;
    ma20?: Array<number | null>;
    ma60?: Array<number | null>;
  };
  macd?: {
    dif?: Array<number | null>;
    dea?: Array<number | null>;
    hist?: Array<number | null>;
  };
  kdj?: {
    k?: Array<number | null>;
    d?: Array<number | null>;
    j?: Array<number | null>;
  };
  boll?: {
    upper?: Array<number | null>;
    mid?: Array<number | null>;
    lower?: Array<number | null>;
  };
  rsi?: Array<number | null>;
};

export type AssetBarsPayload = {
  symbol: string;
  interval: "1d" | "1w" | "1m";
  bars: MarketBar[];
  source: SourceRef;
  fallback_notice?: string | null;
  indicators?: BarIndicators | null;
};

export type RiskCard = {
  symbol: string;
  name: string;
  risk_level: string;
  plain_summary: string;
  evidence: string[];
  risk_counterpoints: string[];
  action_boundary: string;
  content_cta: string;
  source?: SourceRef;
};

export type DataScoreDimension = {
  name: string;
  score: number;
  status: "healthy" | "neutral" | "caution";
  note: string;
};

export type DataScoreCard = {
  symbol: string;
  name: string;
  dimensions: DataScoreDimension[];
  pattern_tags: string[];
  composite_score: number;
  plain_summary: string;
  tracking_condition: string;
  disclaimer: string;
};

export type WatchlistScanItem = {
  symbol: string;
  name: string;
  bucket: "needs_review" | "neutral" | "volatility_up";
  composite_score: number;
  summary: string;
  pattern_tags: string[];
};

export type WatchlistScanResponse = {
  portfolio_summary: string;
  needs_review: WatchlistScanItem[];
  neutral: WatchlistScanItem[];
  volatility_up: WatchlistScanItem[];
  disclaimer: string;
};

export type ReviewNarrativeSection = {
  title: string;
  body: string;
  evidence: string[];
};

export type DailyReviewNarrative = {
  market_date: string;
  headline: string;
  sections: ReviewNarrativeSection[];
  tracking_condition: string;
  disclaimer: string;
};

export type AiAnswer = {
  answer_id: string;
  risk_class: string;
  answer: string;
  citations: { title: string; source_type: string; source_id: string; url?: string; snippet?: string | null }[];
  suggested_actions: { type: string; label: string }[];
  disclaimer: string;
  model_status?: string | null;
  mode?: string | null;
};

export type AiStatus = {
  ollama_online: boolean;
  embedding_ready: boolean;
  model: string;
};

export type StrategySpec = {
  strategy_id: string;
  name: string;
  source: string;
  asset_universe: string[];
  market: string;
  frequency: string;
  entry_rules: { type: string; operator: string; value: number | string; description: string }[];
  exit_rules: { type: string; operator: string; value: number | string; description: string }[];
  tags: string[];
  explanation: string;
  warnings: string[];
  compliance_note: string;
};

export type BacktestReport = {
  backtest_id: string;
  strategy_id: string;
  status: string;
  sample_range: string;
  metrics: Record<string, number>;
  trades: { symbol: string; entry_date: string; exit_date: string; return_pct: number; note: string }[];
  failure_conditions: string[];
  overfit_warning: string;
  disclaimer: string;
};

export type SimulationRun = {
  simulation_id: string;
  strategy_id: string;
  status: string;
  running_days: number;
  last_updated_at: string;
  account: {
    equity: number;
    cash: number;
    positions: { symbol: string; quantity: number; last_price: number; unrealized_return_pct: number }[];
  };
  disclaimer: string;
};

export type KnowledgeLesson = {
  term: string;
  plain_explanation: string;
  why_it_matters: string;
  example: string;
};

export type KnowledgeCategory = {
  id: string;
  label: string;
  count: number;
};

export type KnowledgeArticleSummary = {
  slug: string;
  title: string;
  category: string;
  category_label: string;
  tags: string[];
  summary: string;
  source_path: string;
};

export type KnowledgeArticlesResponse = {
  items: KnowledgeArticleSummary[];
  total: number;
  categories: KnowledgeCategory[];
};

export type KnowledgeArticleDetail = KnowledgeArticleSummary & {
  body: string;
  disclaimer: string;
};

export type ResearchSection = {
  title: string;
  body: string;
  evidence: string[];
};

export type AssetResearchReport = {
  symbol: string;
  name: string;
  generated_at: string;
  trend_view: string;
  key_levels: string[];
  risk_points: string[];
  model_signals: string[];
  sections: ResearchSection[];
  citations: { title: string; source_type: string; source_id: string; url?: string }[];
  disclaimer: string;
};

export type WatchlistRecord = {
  id: number;
  symbol: string;
  name: string;
  note: string;
  status: string;
  added_at: string;
  compliance_note: string;
};

export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fmtPct(value?: number) {
  if (typeof value !== "number") return "-";
  return `${(value * 100).toFixed(2)}%`;
}

export function fmtPrice(value?: number) {
  if (typeof value !== "number") return "-";
  return value.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

export function changeClass(value?: number) {
  if (typeof value !== "number") return "";
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "flat";
}

export function fmtMoney(value?: number) {
  if (typeof value !== "number") return "-";
  return `¥${value.toLocaleString("zh-CN", { maximumFractionDigits: 0 })}`;
}

export async function fetchAssetBars(
  symbol: string,
  interval: "1d" | "1w" | "1m" = "1d",
  limit = 120
) {
  const query = new URLSearchParams({ interval, limit: String(limit) });
  return apiFetch<AssetBarsPayload>(`/api/assets/${symbol}/bars?${query.toString()}`);
}
