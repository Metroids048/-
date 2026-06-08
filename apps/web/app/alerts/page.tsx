"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiNotice } from "../../components/ApiNotice";
import {
  apiFetch,
  type DailyReviewNarrative,
  type WatchlistRecord,
  type WatchlistScanResponse
} from "../lib/api";

type AlertRecord = {
  id: number;
  symbol: string;
  trigger: string;
  channel: string;
  status: string;
  compliance_note: string;
};

export default function AlertsPage() {
  const [watchlist, setWatchlist] = useState<WatchlistRecord[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [scanResult, setScanResult] = useState<WatchlistScanResponse | null>(null);
  const [dailyReview, setDailyReview] = useState<DailyReviewNarrative | null>(null);
  const [symbol, setSymbol] = useState("510300");
  const [trigger, setTrigger] = useState("当风险卡变为高风险时提醒我复盘");
  const [error, setError] = useState("");
  const [scanLoading, setScanLoading] = useState(false);

  async function loadLists() {
    setError("");
    try {
      const [watchPayload, alertPayload, reviewPayload] = await Promise.all([
        apiFetch<{ items: WatchlistRecord[] }>("/api/watchlist"),
        apiFetch<AlertRecord[]>("/api/alerts"),
        apiFetch<DailyReviewNarrative>("/api/review/daily")
      ]);
      setWatchlist(watchPayload.items);
      setAlerts(alertPayload);
      setDailyReview(reviewPayload);
    } catch (err) {
      setError(err instanceof Error ? `预警复盘接口不可用：${err.message}` : "预警复盘接口不可用，请稍后重试。");
    }
  }

  async function handleScanWatchlist() {
    setScanLoading(true);
    setError("");
    try {
      const payload = await apiFetch<WatchlistScanResponse>("/api/watchlist/scan", { method: "POST" });
      setScanResult(payload);
    } catch (err) {
      setError(err instanceof Error ? `扫描失败：${err.message}` : "观察列表扫描失败，请稍后重试。");
    } finally {
      setScanLoading(false);
    }
  }

  async function createAlert(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await apiFetch<AlertRecord>("/api/alerts", {
        method: "POST",
        body: JSON.stringify({ symbol, trigger, channel: "in_app" })
      });
      await loadLists();
    } catch (err) {
      setError(err instanceof Error ? `创建提醒失败：${err.message}` : "创建提醒失败，请稍后重试。");
    }
  }

  useEffect(() => {
    void loadLists();
  }, []);

  function renderScanBucket(title: string, items: WatchlistScanResponse["needs_review"]) {
    if (!items.length) return null;
    return (
      <div className="list-stack compact-list">
        <strong>{title}</strong>
        {items.map((item) => (
          <div className="list-row" key={item.symbol}>
            <strong>{item.symbol} / {item.name} · 综合分 {item.composite_score}</strong>
            <p>{item.summary}</p>
            {item.pattern_tags.length ? <small>模式：{item.pattern_tags.join(" / ")}</small> : null}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">预警复盘</p>
          <h1>只提醒，不自动交易</h1>
          <p>这里管理观察列表、风险提醒和复盘入口。任何提醒都不能被解释为买卖指令。</p>
        </div>
        <button type="button" onClick={() => void handleScanWatchlist()} disabled={scanLoading}>
          {scanLoading ? "扫描中…" : "一键扫描观察列表"}
        </button>
      </section>

      <ApiNotice message={error} onRetry={loadLists} />

      {scanResult ? (
        <section className="panel">
          <p className="eyebrow">组合扫描摘要</p>
          <h2>{scanResult.portfolio_summary}</h2>
          {renderScanBucket("需优先复盘", scanResult.needs_review)}
          {renderScanBucket("波动/情绪抬升", scanResult.volatility_up)}
          {renderScanBucket("数据中性", scanResult.neutral)}
          <p className="fine-print">{scanResult.disclaimer}</p>
        </section>
      ) : null}

      {dailyReview ? (
        <section className="panel">
          <div className="section-title">
            <p className="eyebrow">今日复盘</p>
            <h2>{dailyReview.headline}</h2>
          </div>
          <div className="list-stack">
            {dailyReview.sections.map((section) => (
              <div className="list-row" key={section.title}>
                <strong>{section.title}</strong>
                <p>{section.body}</p>
                <small>证据：{section.evidence.join(" / ")}</small>
              </div>
            ))}
          </div>
          <p className="lead">{dailyReview.tracking_condition}</p>
          <p className="fine-print">{dailyReview.disclaimer}</p>
        </section>
      ) : null}

      <section className="content-grid two">
        <article className="panel">
          <p className="eyebrow">观察列表</p>
          <h2>当前标的</h2>
          <div className="list-stack">
            {watchlist.map((item) => (
              <div className="list-row" key={item.id}>
                <strong>{item.symbol} / {item.name}</strong>
                <p>{item.note}</p>
                <small>{item.compliance_note}</small>
              </div>
            ))}
          </div>
        </article>

        <form className="panel form-panel" onSubmit={createAlert}>
          <p className="eyebrow">创建提醒</p>
          <label>
            标的代码
            <input value={symbol} onChange={(event) => setSymbol(event.target.value)} />
          </label>
          <label>
            提醒条件
            <textarea value={trigger} onChange={(event) => setTrigger(event.target.value)} />
          </label>
          <button type="submit">创建提醒</button>
        </form>
      </section>

      <section className="panel">
        <p className="eyebrow">提醒记录</p>
        <div className="list-stack">
          {alerts.length ? alerts.map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.symbol} / {item.status}</strong>
              <p>{item.trigger}</p>
              <small>{item.compliance_note}</small>
            </div>
          )) : <div className="empty-panel">暂无提醒。创建后会出现在这里。</div>}
        </div>
      </section>
    </div>
  );
}
