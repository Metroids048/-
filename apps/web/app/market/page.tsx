"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiNotice } from "../../components/ApiNotice";
import { AssetSearch } from "../../components/AssetSearch";
import { IndexSparkCard } from "../../components/market/IndexSparkCard";
import { SectorTreemap } from "../../components/market/SectorTreemap";
import {
  apiFetch,
  changeClass,
  fmtPct,
  type DataScoreCard,
  type MarketHeatmapResponse,
  type MarketIndicesResponse,
  type MarketIndustriesResponse,
  type MarketSummary,
  type SourceRef
} from "../lib/api";

const HOT_ETF_SYMBOLS = ["510300", "159915", "512880", "518880"];

function SourceMeta({ source, updatedAt }: { source?: SourceRef | null; updatedAt?: string | null }) {
  if (!source && !updatedAt) return null;
  return (
    <p className="source-meta">
      来源 {source?.source_name ?? "未知"}
      {updatedAt ? ` · 更新 ${updatedAt}` : null}
      {source?.quality_status && source.quality_status !== "ok" ? ` · 质量 ${source.quality_status}` : null}
    </p>
  );
}

export default function MarketPage() {
  const [market, setMarket] = useState<MarketSummary | null>(null);
  const [indices, setIndices] = useState<MarketIndicesResponse | null>(null);
  const [heatmap, setHeatmap] = useState<MarketHeatmapResponse | null>(null);
  const [industries, setIndustries] = useState<MarketIndustriesResponse | null>(null);
  const [etfScores, setEtfScores] = useState<DataScoreCard[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadMarket() {
    setLoading(true);
    setError("");
    try {
      const [summary, indexPayload, heatmapPayload, industryPayload, ...scoreCards] = await Promise.all([
        apiFetch<MarketSummary>("/api/market/summary"),
        apiFetch<MarketIndicesResponse>("/api/market/indices"),
        apiFetch<MarketHeatmapResponse>("/api/market/heatmap"),
        apiFetch<MarketIndustriesResponse>("/api/market/industries"),
        ...HOT_ETF_SYMBOLS.map((symbol) => apiFetch<DataScoreCard>(`/api/assets/${symbol}/data-score`))
      ]);
      setMarket(summary);
      setIndices(indexPayload);
      setHeatmap(heatmapPayload);
      setIndustries(industryPayload);
      setEtfScores(scoreCards);
    } catch (err) {
      setMarket(null);
      setIndices(null);
      setHeatmap(null);
      setIndustries(null);
      setEtfScores([]);
      setError(err instanceof Error ? `市场接口不可用：${err.message}` : "市场接口不可用，请确认后端已启动。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadMarket();
  }, []);

  return (
    <div className="page-stack market-dashboard">
      <section className="page-header">
        <div>
          <p className="eyebrow">市场看板</p>
          <h1>今天市场怎么看</h1>
          <p>{market?.headline || "连接后端后展示指数、板块热力与 ETF 雷达。"}</p>
        </div>
        <AssetSearch compact />
      </section>

      <ApiNotice message={error} onRetry={loadMarket} />

      {loading ? <div className="empty-panel">市场数据加载中…</div> : null}

      {!loading && indices ? (
        <section className="panel dashboard-section">
          <div className="section-title">
            <div>
              <p className="eyebrow">主要指数</p>
              <h2>宽基指数快照</h2>
            </div>
            <SourceMeta source={indices.source} updatedAt={indices.updated_at} />
          </div>
          {indices.fallback_notice ? <p className="fine-print">{indices.fallback_notice}</p> : null}
          <div className="index-grid">
            {indices.items.map((item) => (
              <IndexSparkCard key={item.code} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      {!loading && heatmap ? (
        <section className="panel dashboard-section">
          <div className="section-title">
            <div>
              <p className="eyebrow">板块热力</p>
              <h2>行业涨跌 Treemap</h2>
            </div>
            <SourceMeta source={heatmap.source} updatedAt={heatmap.updated_at} />
          </div>
          <p className="legend-row">
            <span className="legend-chip up">涨</span>
            <span className="legend-chip down">跌</span>
            <span className="fine-print">A 股配色：红涨绿跌，仅作数据解释。</span>
          </p>
          {heatmap.fallback_notice ? <p className="fine-print">{heatmap.fallback_notice}</p> : null}
          <SectorTreemap items={heatmap.items} />
        </section>
      ) : null}

      {!loading && (etfScores.length > 0 || market) ? (
        <section className="panel dashboard-section">
          <div className="section-title">
            <div>
              <p className="eyebrow">ETF 雷达</p>
              <h2>热门 ETF 多维观察</h2>
            </div>
            {etfScores[0]?.disclaimer ? <p className="fine-print">数据评分口径见各维度说明</p> : null}
          </div>
          <div className="table-scroll">
            <table className="radar-table">
              <thead>
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>综合分</th>
                  <th>量能</th>
                  <th>资金</th>
                  <th>情绪</th>
                  <th>模式标签</th>
                </tr>
              </thead>
              <tbody>
                {etfScores.map((row) => (
                  <tr key={row.symbol}>
                    <td>
                      <Link href={`/assets/${row.symbol}`}>{row.symbol}</Link>
                    </td>
                    <td>{row.name}</td>
                    <td>
                      <strong>{row.composite_score}</strong>
                    </td>
                    {row.dimensions.slice(0, 3).map((dim) => (
                      <td key={`${row.symbol}-${dim.name}`}>
                        <span className={`score-chip ${dim.status}`}>{dim.score}</span>
                      </td>
                    ))}
                    <td>{row.pattern_tags.join(" / ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {!loading && market ? (
        <section className="content-grid two dashboard-section">
          <article className="panel">
            <div className="section-title">
              <div>
                <p className="eyebrow">可解释信号</p>
                <h2>信号卡</h2>
              </div>
              <SourceMeta source={market.source} updatedAt={market.updated_at} />
            </div>
            <div className="signal-grid">
              {market.signal_cards.map((card) => (
                <div className="signal-card" key={card.symbol}>
                  <div className="signal-card-head">
                    <strong>{card.title}</strong>
                    <span className="confidence-chip">{card.confidence}</span>
                  </div>
                  <p>{card.reason}</p>
                  <small>证据：{card.evidence.join(" / ")}</small>
                  <small>反例：{card.risk_counterpoint}</small>
                  <Link href={`/assets/${card.symbol}`}>查看标的详情</Link>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="section-title">
              <div>
                <p className="eyebrow">行业温度</p>
                <h2>板块观察</h2>
              </div>
              <SourceMeta source={industries?.source} updatedAt={industries?.updated_at} />
            </div>
            <div className="list-stack">
              {(industries?.items ?? []).map((item) => (
                <div className="industry-row" key={item.name}>
                  <div>
                    <strong>{item.name}</strong>
                    <p>{item.explanation}</p>
                    <small>反例：{item.risk_counterpoint}</small>
                  </div>
                  <span className={`temp ${item.temperature} ${changeClass(item.change_pct)}`}>
                    {item.temperature} / {fmtPct(item.change_pct)}
                  </span>
                </div>
              ))}
            </div>
            {market.pre_market_brief ? (
              <div className="brief-box">
                <strong>{market.pre_market_brief.direction_label}</strong>
                <p>{market.pre_market_brief.action_mantra}</p>
                <small>{market.pre_market_brief.methodology_note}</small>
              </div>
            ) : null}
          </article>
        </section>
      ) : null}

      {!loading && !market && !error ? (
        <div className="empty-panel">暂无市场数据。请启动后端：uvicorn apps.api.alpha_sim.main:app --port 8000</div>
      ) : null}
    </div>
  );
}
