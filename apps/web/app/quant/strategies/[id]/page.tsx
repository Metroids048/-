"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ApiNotice } from "../../../../components/ApiNotice";
import { apiFetch, fmtMoney, fmtPct } from "../../../lib/api";

type StrategyCardResponse = {
  strategy: {
    strategy_id: string;
    name: string;
    explanation: string;
    tags: string[];
    compliance_note: string;
  };
  backtest: {
    metrics: Record<string, number>;
    failure_conditions: string[];
    overfit_warning: string;
  };
  simulation: {
    status: string;
    running_days: number;
    account: {
      equity: number;
      cash: number;
    };
  } | null;
  risk_counterexamples: string[];
  disclaimer: string;
};

export default function QuantStrategyDetailPage() {
  const params = useParams<{ id: string }>();
  const strategyId = useMemo(() => (typeof params?.id === "string" ? params.id : ""), [params]);
  const [payload, setPayload] = useState<StrategyCardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDetail(id: string) {
    if (!id) return;
    setLoading(true);
    setError("");
    try {
      const detail = await apiFetch<StrategyCardResponse>(`/api/strategies/${id}`);
      setPayload(detail);
    } catch (err) {
      setPayload(null);
      setError(err instanceof Error ? `策略详情接口不可用：${err.message}` : "策略详情接口不可用。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (strategyId) {
      void loadDetail(strategyId);
    }
  }, [strategyId]);

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">策略详情</p>
          <h1>{payload?.strategy.name || strategyId || "加载中..."}</h1>
          <p>展示策略逻辑、回测与虚拟模拟表现，帮助你复盘而不是做实时交易决策。</p>
        </div>
        <div className="button-row">
          <Link className="entry-card inline-cta" href="/quant">返回量化模拟</Link>
          <Link className="entry-card inline-cta" href={`/strategy-lab?strategy_id=${strategyId}`}>去策略实验室</Link>
        </div>
      </section>

      <ApiNotice message={error} onRetry={() => loadDetail(strategyId)} />
      {loading ? <div className="empty-panel">策略详情加载中…</div> : null}

      {!loading && payload ? (
        <>
          <section className="content-grid two">
            <article className="panel">
              <p className="eyebrow">策略摘要</p>
              <h2>{payload.strategy.name}</h2>
              <p>{payload.strategy.explanation}</p>
              <div className="tag-row">{payload.strategy.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
              <p className="fine-print">{payload.strategy.compliance_note}</p>
            </article>

            <article className="panel">
              <p className="eyebrow">回测与模拟</p>
              <div className="metric-strip compact">
                <article><span>回测总收益</span><strong>{fmtPct(payload.backtest.metrics.total_return)}</strong></article>
                <article><span>回测最大回撤</span><strong>{fmtPct(payload.backtest.metrics.max_drawdown)}</strong></article>
                <article><span>运行天数</span><strong>{payload.simulation?.running_days ?? 0}</strong></article>
              </div>
              {payload.simulation ? (
                <p>
                  虚拟状态 {payload.simulation.status} / 虚拟权益 {fmtMoney(payload.simulation.account.equity)} / 虚拟现金{" "}
                  {fmtMoney(payload.simulation.account.cash)}
                </p>
              ) : (
                <p>该策略暂未加入模拟盘，可在策略实验室继续推进。</p>
              )}
            </article>
          </section>

          <section className="content-grid two">
            <article className="panel">
              <p className="eyebrow">失效条件</p>
              <div className="list-stack compact-list">
                {payload.backtest.failure_conditions.map((item) => <small key={item}>- {item}</small>)}
              </div>
              <p className="fine-print">{payload.backtest.overfit_warning}</p>
            </article>
            <article className="panel">
              <p className="eyebrow">风险反例</p>
              <div className="list-stack compact-list">
                {payload.risk_counterexamples.map((item) => <small key={item}>- {item}</small>)}
              </div>
              <p className="fine-print">{payload.disclaimer}</p>
            </article>
          </section>
        </>
      ) : null}
    </div>
  );
}
