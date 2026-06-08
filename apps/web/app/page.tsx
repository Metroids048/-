"use client";

import Link from "next/link";
import type { Route } from "next";
import { useEffect, useState } from "react";
import { ApiNotice } from "../components/ApiNotice";
import { AssetSearch } from "../components/AssetSearch";
import { apiFetch, fmtMoney, fmtPct } from "./lib/api";

type LeaderboardItem = {
  strategy_id: string;
  simulation_id: string;
  name: string;
  paper_return: number;
  max_drawdown: number;
  running_days: number;
  total_score: number;
};

type LeaderboardResponse = {
  title: string;
  items: LeaderboardItem[];
  disclaimer: string;
};

type HomeStats = {
  running_strategies: number;
  virtual_capital: number;
};

const taskCards: { href: Route; title: string; body: string; meta: string }[] = [
  { href: "/quant", title: "量化模拟", body: "查看榜单与运行中模拟盘，围观策略长期表现。", meta: "核心看板" },
  { href: "/strategy-lab", title: "创建策略", body: "把投资想法转成规则、回测并加入虚拟模拟盘。", meta: "核心闭环" },
  { href: "/strategy-lab", title: "策略实验室", body: "早盘想追？先用虚拟盘跑一遍同类规则，验证冲动再观察。", meta: "防冲动入口" },
  { href: "/market", title: "今日市场", body: "指数、行业和可解释信号卡，帮助理解市场背景。", meta: "辅助层" },
  { href: "/assets", title: "标的研究", body: "K线、AI研报、风险卡和问问Alpha。", meta: "投研入口" }
];

export default function HomePage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const board = await apiFetch<LeaderboardResponse>("/api/leaderboards?type=stability");
      setLeaderboard(board);
      const virtualCapital = board.items.reduce((sum, item) => sum + 100000 * (1 + item.paper_return), 0);
      setStats({
        running_strategies: board.items.length,
        virtual_capital: Math.round(virtualCapital)
      });
    } catch (err) {
      setLeaderboard(null);
      setStats(null);
      setError(err instanceof Error ? `首页数据接口不可用：${err.message}` : "首页数据接口不可用，请确认后端已启动。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  return (
    <div className="page-stack">
      <section className="hero-panel compact-hero">
        <div>
          <p className="eyebrow">Alpha模拟场</p>
          <h1>虚拟资金模拟：用 AI 量化策略做非实盘验证</h1>
          <p className="lead">
            首页展示真实运行中的模拟策略和榜单。主链路：创建策略 → 回测 → 加入模拟盘 → 持续围观表现。
          </p>
          <p className="fine-print">合规边界：不构成投资建议，不接真实资金。</p>
        </div>
        <div className="hero-search">
          <AssetSearch initialSymbol="510300" />
          <div className="button-row">
            <Link className="entry-card inline-cta" href="/strategy-lab">创建策略</Link>
            <Link className="entry-card inline-cta" href="/quant">查看榜单详情</Link>
          </div>
        </div>
      </section>

      <ApiNotice message={error} onRetry={loadDashboard} />

      {loading ? <div className="empty-panel">控制台数据加载中…</div> : null}

      {!loading && stats ? (
        <section className="metric-strip">
          <article>
            <span>运行策略</span>
            <strong>{stats.running_strategies}</strong>
          </article>
          <article>
            <span>虚拟资金合计</span>
            <strong>{fmtMoney(stats.virtual_capital)}</strong>
          </article>
          <article>
            <span>榜单类型</span>
            <strong>{leaderboard?.title || "稳定性榜"}</strong>
          </article>
        </section>
      ) : null}

      {!loading && leaderboard ? (
        <section className="panel">
          <div className="section-title">
            <p className="eyebrow">策略榜单</p>
            <h2>{leaderboard.title}</h2>
          </div>
          <div className="list-stack">
            {leaderboard.items.slice(0, 5).map((item) => (
              <div className="list-row" key={item.simulation_id}>
                <strong>{item.name}</strong>
                <p>
                  虚拟收益 {fmtPct(item.paper_return)} / 最大回撤 {fmtPct(item.max_drawdown)} / 运行 {item.running_days} 天
                </p>
                <small>评分 {item.total_score.toFixed(1)}。{leaderboard.disclaimer}</small>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="task-entry-grid" aria-label="工作台任务入口">
        {taskCards.map((card) => (
          <Link className="entry-card" href={card.href} key={card.title}>
            <span>{card.meta}</span>
            <strong>{card.title}</strong>
            <p>{card.body}</p>
          </Link>
        ))}
      </section>

      <section className="split-panel">
        <article>
          <p className="eyebrow">核心闭环</p>
          <h2>想法 → 规则 → 回测 → 模拟盘 → 榜单</h2>
          <p>所有结论都必须可追溯、可复盘，并明确不是买卖建议。</p>
        </article>
        <article>
          <p className="eyebrow">防冲动验证</p>
          <h2>差点追高？先开虚拟模拟盘</h2>
          <p>把早盘冲动转成可回测规则，用虚拟资金验证后再决定是否持续观察。</p>
        </article>
      </section>
    </div>
  );
}
