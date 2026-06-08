"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiNotice } from "../../components/ApiNotice";
import { apiFetch, fmtMoney, fmtPct } from "../lib/api";

type LeaderboardType = "stability" | "performance" | "risk_control" | "longevity";

type LeaderboardItem = {
  strategy_id: string;
  simulation_id: string;
  name: string;
  strategy_type: string;
  paper_return: number;
  max_drawdown: number;
  running_days: number;
  total_score: number;
  risk_level: string;
};

type LeaderboardResponse = {
  leaderboard_type: string;
  title: string;
  items: LeaderboardItem[];
  disclaimer: string;
};

type SimulationSummary = {
  simulation_id: string;
  strategy_id: string;
  name: string;
  status: string;
  paper_return: number;
  max_drawdown: number;
  running_days: number;
  started_at: string;
};

type SimulationsResponse = {
  items: SimulationSummary[];
};

const boardTabs: { type: LeaderboardType; label: string; hint: string }[] = [
  { type: "stability", label: "稳定性", hint: "综合稳定 + 风险事件" },
  { type: "performance", label: "表现", hint: "虚拟收益优先" },
  { type: "risk_control", label: "风控", hint: "控制回撤优先" },
  { type: "longevity", label: "长跑", hint: "持续运行天数" }
];

export default function QuantHubPage() {
  const [boardType, setBoardType] = useState<LeaderboardType>("stability");
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadQuantHub(type: LeaderboardType) {
    setLoading(true);
    setError("");
    try {
      const [board, sims] = await Promise.all([
        apiFetch<LeaderboardResponse>(`/api/leaderboards?type=${type}`),
        apiFetch<SimulationsResponse>("/api/simulations")
      ]);
      setLeaderboard(board);
      setSimulations(sims.items);
    } catch (err) {
      setLeaderboard(null);
      setSimulations([]);
      setError(err instanceof Error ? `量化专区接口不可用：${err.message}` : "量化专区接口不可用，请确认后端已启动。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadQuantHub(boardType);
  }, [boardType]);

  return (
    <div className="page-stack">
      <section className="hero-panel compact-hero">
        <div>
          <p className="eyebrow">Alpha量化专区</p>
          <h1>虚拟资金策略模拟场</h1>
          <p className="lead">
            这里展示策略在虚拟账户中的持续运行表现，核心是可观察、可复盘，不是买卖建议入口。
          </p>
          <p className="fine-print">合规提示：虚拟资金模拟，不构成投资建议，不接真实资金。</p>
        </div>
        <div className="hero-search">
          <div className="metric-strip compact">
            <article>
              <span>运行中模拟盘</span>
              <strong>{simulations.length}</strong>
            </article>
            <article>
              <span>榜单类型</span>
              <strong>{leaderboard?.title || "-"}</strong>
            </article>
            <article>
              <span>入口动作</span>
              <strong>创建策略</strong>
            </article>
          </div>
          <div className="button-row">
            <Link className="entry-card inline-cta" href="/strategy-lab">创建策略</Link>
            <Link className="entry-card inline-cta" href="/strategy-lab">进入策略实验室</Link>
          </div>
        </div>
      </section>

      <ApiNotice message={error} onRetry={() => loadQuantHub(boardType)} />

      {loading ? <div className="empty-panel">量化专区数据加载中…</div> : null}

      {!loading && leaderboard ? (
        <section className="panel">
          <div className="section-title horizontal">
            <div>
              <p className="eyebrow">榜单</p>
              <h2>{leaderboard.title}</h2>
            </div>
            <small>{leaderboard.disclaimer}</small>
          </div>

          <div className="ths-kline-tabs secondary">
            {boardTabs.map((tab) => (
              <button
                className={boardType === tab.type ? "active" : ""}
                key={tab.type}
                onClick={() => setBoardType(tab.type)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="list-stack">
            {leaderboard.items.length ? (
              leaderboard.items.map((item) => (
                <div className="list-row" key={item.simulation_id}>
                  <div className="section-title horizontal">
                    <div>
                      <strong>{item.name}</strong>
                      <small>{item.strategy_type} · {boardTabs.find((tab) => tab.type === boardType)?.hint}</small>
                    </div>
                    <Link href={`/quant/strategies/${item.strategy_id}`}>查看策略</Link>
                  </div>
                  <p>
                    虚拟收益 {fmtPct(item.paper_return)} / 最大回撤 {fmtPct(item.max_drawdown)} / 运行 {item.running_days} 天
                  </p>
                  <small>综合评分 {item.total_score.toFixed(1)}，风险等级 {item.risk_level}。</small>
                </div>
              ))
            ) : (
              <div className="empty-panel">当前榜单暂无可展示策略。</div>
            )}
          </div>
        </section>
      ) : null}

      {!loading ? (
        <section className="panel">
          <div className="section-title">
            <p className="eyebrow">运行中模拟盘</p>
            <h2>正在运行的虚拟账户</h2>
          </div>
          <div className="list-stack">
            {simulations.length ? (
              simulations.map((run) => (
                <div className="list-row" key={run.simulation_id}>
                  <div className="section-title horizontal">
                    <strong>{run.name}</strong>
                    <Link href={`/quant/strategies/${run.strategy_id}`}>查看详情</Link>
                  </div>
                  <p>
                    状态 {run.status} / 虚拟收益 {fmtPct(run.paper_return)} / 最大回撤 {fmtPct(run.max_drawdown)} /
                    运行 {run.running_days} 天
                  </p>
                  <small>开始时间 {run.started_at}。仅用于策略观察，不构成投资建议。</small>
                </div>
              ))
            ) : (
              <div className="empty-panel">暂无运行中的模拟盘，可先去策略实验室创建并加入模拟。</div>
            )}
          </div>
        </section>
      ) : null}

      <section className="split-panel">
        <article>
          <p className="eyebrow">快速入口</p>
          <h2>从想法到模拟，先验证再观察</h2>
          <p>建议路径：策略实验室生成规则 → 回测 → 加入虚拟模拟盘 → 回到本页围观看板。</p>
        </article>
        <article>
          <p className="eyebrow">合规提醒</p>
          <h2>仅虚拟资金，不接真实资金</h2>
          <p>榜单与模拟盘只展示虚拟表现，不提供跟买、代客理财或自动下单能力。</p>
        </article>
      </section>
    </div>
  );
}
