"use client";

import { FormEvent, useState } from "react";
import { ApiNotice } from "../../components/ApiNotice";
import { apiFetch, fmtMoney, fmtPct, type BacktestReport, type SimulationRun, type StrategySpec } from "../lib/api";

export default function StrategyLabPage() {
  const [prompt, setPrompt] = useState("沪深300ETF回撤5%后分批观察，反弹后退出虚拟仓位");
  const [symbols, setSymbols] = useState("510300");
  const [strategy, setStrategy] = useState<StrategySpec | null>(null);
  const [backtest, setBacktest] = useState<BacktestReport | null>(null);
  const [simulation, setSimulation] = useState<SimulationRun | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");

  async function handleCompileStrategy(event: FormEvent) {
    event.preventDefault();
    setLoading("compile");
    setError("");
    try {
      const payload = await apiFetch<StrategySpec>("/api/strategies/compile", {
        method: "POST",
        body: JSON.stringify({
          prompt,
          preferred_assets: symbols.split(",").map((item) => item.trim()).filter(Boolean),
          risk_level: "moderate",
          market: "CN_A_ETF"
        })
      });
      setStrategy(payload);
      setBacktest(null);
      setSimulation(null);
    } catch (err) {
      setError(err instanceof Error ? `策略接口不可用：${err.message}` : "策略接口不可用，请确认后端已启动。");
    } finally {
      setLoading("");
    }
  }

  async function handleRunBacktest() {
    if (!strategy) {
      setError("请先生成策略规则。");
      return;
    }
    setLoading("backtest");
    setError("");
    try {
      const payload = await apiFetch<BacktestReport>("/api/backtests", {
        method: "POST",
        body: JSON.stringify({ strategy, initial_cash: 100000, fee_rate: 0.0003, slippage_bps: 5 })
      });
      setBacktest(payload);
    } catch (err) {
      setError(err instanceof Error ? `回测接口不可用：${err.message}` : "回测接口不可用。");
    } finally {
      setLoading("");
    }
  }

  async function handleJoinSimulation() {
    if (!strategy || !backtest) {
      setError("请先完成策略生成和回测。");
      return;
    }
    setLoading("simulation");
    setError("");
    try {
      const payload = await apiFetch<SimulationRun>("/api/simulations", {
        method: "POST",
        body: JSON.stringify({
          strategy_id: strategy.strategy_id,
          backtest_id: backtest.backtest_id,
          initial_cash: 100000,
          visibility: "public_delayed"
        })
      });
      setSimulation(payload);
    } catch (err) {
      setError(err instanceof Error ? `模拟盘接口不可用：${err.message}` : "模拟盘接口不可用。");
    } finally {
      setLoading("");
    }
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">策略实验</p>
          <h1>验证投资想法，而不是输出买卖指令</h1>
          <p>量化模块是专业能力区：把想法拆成规则、回测、虚拟模拟盘和失败条件，所有结果都不构成投资建议。</p>
          <p className="fine-print">场景提示：早盘想追热点时，可先把冲动写成规则，用虚拟盘验证后再决定是否持续观察。</p>
        </div>
      </section>

      <ApiNotice message={error} />

      <section className="strategy-layout">
        <form className="panel form-panel" onSubmit={handleCompileStrategy}>
          <label>
            投资想法
            <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
          </label>
          <label>
            标的池
            <input value={symbols} onChange={(event) => setSymbols(event.target.value)} />
          </label>
          <div className="button-row">
            <button type="submit" disabled={loading === "compile"}>{loading === "compile" ? "生成中" : "生成规则"}</button>
            <button type="button" onClick={handleRunBacktest} disabled={loading === "backtest" || !strategy}>{loading === "backtest" ? "回测中" : "运行回测"}</button>
            <button type="button" onClick={handleJoinSimulation} disabled={loading === "simulation" || !backtest}>{loading === "simulation" ? "加入中" : "加入模拟盘"}</button>
          </div>
        </form>

        <article className="panel">
          {strategy ? (
            <>
              <p className="eyebrow">规则卡</p>
              <h2>{strategy.name}</h2>
              <p>{strategy.explanation}</p>
              <div className="tag-row">{strategy.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
              <div className="rule-grid">
                <div>
                  <strong>进入规则</strong>
                  {strategy.entry_rules.map((rule) => <small key={rule.type}>{rule.description}</small>)}
                </div>
                <div>
                  <strong>退出规则</strong>
                  {strategy.exit_rules.map((rule) => <small key={rule.type}>{rule.description}</small>)}
                </div>
              </div>
              <p className="fine-print">{strategy.compliance_note}</p>
            </>
          ) : (
            <div className="empty-panel">输入投资想法并点击「生成规则」，后端将把自然语言编译为可回测的结构化规则。</div>
          )}
        </article>
      </section>

      <section className="content-grid two">
        <article className="panel">
          <p className="eyebrow">回测结果</p>
          {backtest ? (
            <>
              <h2>{backtest.status}</h2>
              <div className="metric-strip compact">
                <article><span>总收益</span><strong>{fmtPct(backtest.metrics.total_return)}</strong></article>
                <article><span>最大回撤</span><strong>{fmtPct(backtest.metrics.max_drawdown)}</strong></article>
                <article><span>胜率</span><strong>{fmtPct(backtest.metrics.win_rate)}</strong></article>
              </div>
              <div className="list-stack compact-list">
                {backtest.failure_conditions.map((item) => <small key={item}>失败条件：{item}</small>)}
              </div>
              <p className="fine-print">{backtest.overfit_warning}</p>
            </>
          ) : (
            <div className="empty-panel">完成规则生成后运行回测，查看收益、回撤和失效条件。</div>
          )}
        </article>

        <article className="panel">
          <p className="eyebrow">虚拟模拟盘</p>
          {simulation ? (
            <>
              <h2>{simulation.status}</h2>
              <div className="metric-strip compact">
                <article><span>虚拟权益</span><strong>{fmtMoney(simulation.account.equity)}</strong></article>
                <article><span>虚拟现金</span><strong>{fmtMoney(simulation.account.cash)}</strong></article>
                <article><span>运行天数</span><strong>{simulation.running_days}</strong></article>
              </div>
              <p className="fine-print">{simulation.disclaimer}</p>
            </>
          ) : (
            <div className="empty-panel">先完成回测，再把策略加入虚拟模拟盘持续观察。</div>
          )}
        </article>
      </section>
    </div>
  );
}
