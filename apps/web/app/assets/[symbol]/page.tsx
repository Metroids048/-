"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { ApiNotice } from "../../../components/ApiNotice";
import { AssetSearch } from "../../../components/AssetSearch";
import { ThsKLineChart } from "../../../components/ThsKLineChart";
import {
  apiFetch,
  type AiAnswer,
  type AssetBarsPayload,
  type AssetProfile,
  type AssetResearchReport,
  type RiskCard,
  type DataScoreCard,
  type WatchlistRecord
} from "../../lib/api";

export default function AssetDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = useMemo(() => decodeURIComponent(params.symbol || "510300").toUpperCase(), [params.symbol]);
  const [profile, setProfile] = useState<AssetProfile | null>(null);
  const [barsData, setBarsData] = useState<AssetBarsPayload | null>(null);
  const [riskCard, setRiskCard] = useState<RiskCard | null>(null);
  const [dataScore, setDataScore] = useState<DataScoreCard | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AiAnswer | null>(null);
  const [report, setReport] = useState<AssetResearchReport | null>(null);
  const [reportError, setReportError] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [watchItem, setWatchItem] = useState<WatchlistRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadResearchReport() {
    setReportLoading(true);
    setReportError("");
    try {
      const payload = await apiFetch<AssetResearchReport>(`/api/assets/${symbol}/research-report`);
      setReport(payload);
    } catch (err) {
      setReport(null);
      setReportError(err instanceof Error ? `研报接口不可用：${err.message}` : "研报接口不可用，请稍后重试。");
    } finally {
      setReportLoading(false);
    }
  }

  async function retryAssetLoad() {
    setLoading(true);
    setError("");
    setReport(null);
    setReportError("");
    try {
      const [profilePayload, barsPayload, riskPayload, scorePayload] = await Promise.all([
        apiFetch<AssetProfile>(`/api/assets/${symbol}/profile`),
        apiFetch<AssetBarsPayload>(`/api/assets/${symbol}/bars?interval=1d&limit=120`),
        apiFetch<RiskCard>(`/api/assets/${symbol}/risk-card`),
        apiFetch<DataScoreCard>(`/api/assets/${symbol}/data-score`)
      ]);
      setProfile(profilePayload);
      setBarsData(barsPayload);
      setRiskCard(riskPayload);
      setDataScore(scorePayload);
      setQuestion(`帮我解释 ${profilePayload.name} 最近的K线和风险点`);
      void loadResearchReport();
    } catch (err) {
      setProfile(null);
      setBarsData(null);
      setRiskCard(null);
      setDataScore(null);
      setReport(null);
      setReportError("");
      setError(err instanceof Error ? `标的核心数据接口不可用：${err.message}` : "标的核心数据接口不可用，请确认后端已启动。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void retryAssetLoad();
  }, [symbol]);

  async function handleAskAlpha(event: FormEvent) {
    event.preventDefault();
    if (!profile) return;
    setError("");
    try {
      const payload = await apiFetch<AiAnswer>("/api/ai/ask", {
        method: "POST",
        body: JSON.stringify({
          question,
          entry_point: "asset_detail",
          context: { symbol, asset_name: profile.name }
        })
      });
      setAnswer(payload);
    } catch (err) {
      setError(err instanceof Error ? `问AI接口不可用：${err.message}` : "问AI接口不可用，请稍后重试。");
    }
  }

  async function handleAddWatchlist() {
    if (!profile) return;
    setError("");
    try {
      const payload = await apiFetch<WatchlistRecord>("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          note: `观察${profile.name}的K线、风险卡和行业背景`,
          source: "asset_detail"
        })
      });
      setWatchItem(payload);
    } catch (err) {
      setError(err instanceof Error ? `观察列表接口不可用：${err.message}` : "观察列表接口不可用，请稍后重试。");
    }
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">标的研究</p>
          <h1>{profile?.name || symbol}</h1>
          <p>
            {profile
              ? `${profile.symbol} / ${profile.asset_type} / ${profile.market}。${profile.summary}`
              : "连接后端后展示标的资料、K线和风险卡。"}
          </p>
        </div>
        <AssetSearch initialSymbol={symbol} compact />
      </section>

      <ApiNotice message={error} onRetry={retryAssetLoad} />

      {loading ? <div className="empty-panel">标的数据加载中…</div> : null}

      {!loading && profile && riskCard ? (
        <>
          <section className="asset-layout">
            <article className="panel main-chart-panel">
              <div className="section-title horizontal">
                <div>
                  <p className="eyebrow">K线图</p>
                  <h2>价格、波动和成交量</h2>
                </div>
                <button type="button" onClick={retryAssetLoad} disabled={loading}>
                  刷新
                </button>
              </div>
              {barsData?.bars.length ? (
                <ThsKLineChart key={symbol} symbol={symbol} initialData={barsData} />
              ) : (
                <div className="empty-panel">暂无K线数据。</div>
              )}
            </article>

            <aside className="panel">
              <p className="eyebrow">标的详情</p>
              <h2>{profile.exchange} / {profile.currency}</h2>
              <div className="tag-row">
                {profile.tags.map((tag) => <span key={tag}>{tag}</span>)}
              </div>
              <dl className="info-list">
                <div><dt>状态</dt><dd>{profile.status}</dd></div>
                <div><dt>数据源</dt><dd>{profile.source.source_name}</dd></div>
                <div><dt>质量</dt><dd>{profile.source.quality_status}</dd></div>
                <div><dt>数据日期</dt><dd>{profile.source.data_time || "-"}</dd></div>
              </dl>
              <button type="button" onClick={handleAddWatchlist}>加入观察</button>
              {watchItem ? <p className="success-line">已加入观察：{watchItem.name}，状态 {watchItem.status}</p> : null}
            </aside>
          </section>

          <section className="panel">
            <div className="section-title horizontal">
              <div>
                <p className="eyebrow">AI 研报</p>
                <h2>{profile.name} 观察研报</h2>
              </div>
              <button type="button" onClick={() => void loadResearchReport()} disabled={reportLoading}>
                {reportLoading ? "加载中…" : "重试研报"}
              </button>
            </div>
            {reportError ? (
              <div className="list-row">
                <strong>研报暂时不可用</strong>
                <p>{reportError}</p>
                <button type="button" onClick={() => void loadResearchReport()} disabled={reportLoading}>
                  {reportLoading ? "重试中…" : "重试加载"}
                </button>
              </div>
            ) : null}
            {report ? (
              <>
                <p>{report.trend_view}</p>
                <div className="tag-row">
                  {report.model_signals.map((signal) => <span key={signal}>{signal}</span>)}
                </div>
                <div className="list-stack compact-list">
                  {report.sections.map((section) => (
                    <div className="list-row" key={section.title}>
                      <strong>{section.title}</strong>
                      <p>{section.body}</p>
                      <small>证据：{section.evidence.join(" / ")}</small>
                    </div>
                  ))}
                </div>
                <p className="fine-print">{report.disclaimer}</p>
              </>
            ) : null}
            {!report && !reportError && reportLoading ? <div className="empty-panel">研报加载中…</div> : null}
            {!report && !reportError && !reportLoading ? <div className="empty-panel">暂无研报内容。</div> : null}
          </section>

          <section className="panel">
            <div className="section-title">
              <p className="eyebrow">多维数据评分</p>
              <h2>综合分 {dataScore?.composite_score ?? "-"} / 100</h2>
            </div>
            {dataScore ? (
              <>
                <p>{dataScore.plain_summary}</p>
                <div className="tag-row">
                  {dataScore.pattern_tags.map((tag) => <span key={tag}>{tag}</span>)}
                </div>
                <div className="list-stack compact-list">
                  {dataScore.dimensions.map((dim) => (
                    <div className="list-row" key={dim.name}>
                      <strong>{dim.name} · {dim.score} · {dim.status}</strong>
                      <p>{dim.note}</p>
                    </div>
                  ))}
                </div>
                <p className="fine-print">{dataScore.tracking_condition}</p>
                <p className="fine-print">{dataScore.disclaimer}</p>
              </>
            ) : (
              <div className="empty-panel">数据评分加载中…</div>
            )}
          </section>

          <section className="content-grid two">
            <article className="panel">
              <div className="section-title">
                <p className="eyebrow">风险卡</p>
                <h2>{riskCard.risk_level}</h2>
              </div>
              <p>{riskCard.plain_summary}</p>
              <div className="evidence-grid">
                {riskCard.evidence.map((item) => <span key={item}>{item}</span>)}
              </div>
              <div className="list-stack compact-list">
                {riskCard.risk_counterpoints.map((item) => <small key={item}>反例：{item}</small>)}
              </div>
              <p className="fine-print">{riskCard.action_boundary}</p>
            </article>

            <article className="panel">
              <div className="section-title">
                <p className="eyebrow">问问 Alpha</p>
                <h2>围绕当前标的追问</h2>
              </div>
              <form className="ask-form" onSubmit={handleAskAlpha}>
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
                <button type="submit">提问</button>
              </form>
              {answer ? (
                <div className="answer-box">
                  <strong>{answer.risk_class}</strong>
                  <p>{answer.answer}</p>
                  <small>引用：{answer.citations.map((item) => item.title).join(" / ")}</small>
                </div>
              ) : (
                <div className="empty-panel">还没有追问。可以问“为什么波动变大”“风险卡怎么理解”“数据源是否足够”。</div>
              )}
            </article>
          </section>
        </>
      ) : null}
    </div>
  );
}
