"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiNotice } from "../../components/ApiNotice";
import { apiFetch, type AiAnswer, type AiStatus } from "../lib/api";

function parseInjectedContext(rawContext: string | null): Record<string, string> {
  if (!rawContext) return {};
  let decoded = rawContext;
  try {
    decoded = decodeURIComponent(rawContext);
  } catch {
    decoded = rawContext;
  }
  try {
    const parsed = JSON.parse(decoded) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { raw_context: decoded };
    }
    const context: Record<string, string> = {};
    for (const [key, value] of Object.entries(parsed)) {
      context[key] = String(value);
    }
    return context;
  } catch {
    return { raw_context: decoded };
  }
}

function modelStatusClass(status: string | null | undefined): string {
  if (!status) return "neutral";
  if (status === "online" || status === "full_rag") return "online";
  if (status === "blocked") return "offline";
  return "neutral";
}

function modelStatusLabel(status: string | null | undefined): string {
  const labels: Record<string, string> = {
    online: "模型在线",
    offline: "检索模式（模型离线）",
    no_evidence: "无足够依据",
    empty_output: "模型无输出",
    generation_disabled: "仅检索",
    blocked: "合规拒答",
  };
  return labels[status || ""] || status || "未知";
}

export default function AiPage() {
  const [question, setQuestion] = useState("");
  const [contextPayload, setContextPayload] = useState<Record<string, string>>({});
  const [answer, setAnswer] = useState<AiAnswer | null>(null);
  const [error, setError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const rawQuestion = params.get("q");
    if (rawQuestion) {
      try {
        setQuestion(decodeURIComponent(rawQuestion).trim());
      } catch {
        setQuestion(rawQuestion.trim());
      }
    }
    setContextPayload(parseInjectedContext(params.get("context")));
  }, []);

  useEffect(() => {
    async function loadStatus() {
      setStatusError("");
      try {
        const payload = await apiFetch<AiStatus>("/api/ai/status");
        setAiStatus(payload);
      } catch (err) {
        setAiStatus(null);
        setStatusError(err instanceof Error ? `AI 状态接口不可用：${err.message}` : "AI 状态接口不可用，请稍后重试。");
      }
    }
    void loadStatus();
  }, []);

  async function ask(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<AiAnswer>("/api/ai/ask", {
        method: "POST",
        body: JSON.stringify({ question, entry_point: "ai_page", context: contextPayload }),
      });
      setAnswer(payload);
    } catch (err) {
      setError(err instanceof Error ? `问AI接口不可用：${err.message}` : "问AI接口不可用，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">问 AI</p>
          <h1>先要证据，再要解释</h1>
          <p>全局问答适合解释市场、标的、风险卡和策略实验。涉及买卖点、收益承诺和跟单的问题会被拒答。</p>
          <div className="ai-status-bar">
            <span className={`status-badge ${aiStatus?.ollama_online ? "online" : "offline"}`}>
              {aiStatus?.ollama_online ? "Ollama 在线" : "Ollama 离线"}
            </span>
            <span className={`status-badge ${aiStatus?.embedding_ready ? "online" : "neutral"}`}>
              {aiStatus?.embedding_ready ? "Embedding 已就绪" : "关键词检索兜底"}
            </span>
            <span className="status-badge neutral">模型：{aiStatus?.model || "-"}</span>
          </div>
          {Object.keys(contextPayload).length ? (
            <small className="fine-print">上下文注入：{Object.entries(contextPayload).map(([key, value]) => `${key}=${value}`).join(" ; ")}</small>
          ) : null}
        </div>
      </section>

      <ApiNotice message={error} />
      <ApiNotice message={statusError} />

      <section className="content-grid two">
        <form className="panel form-panel" onSubmit={ask}>
          <label>
            问题
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
          </label>
          <button type="submit" disabled={loading}>{loading ? "回答中" : "提问"}</button>
        </form>

        <article className="panel">
          <p className="eyebrow">回答</p>
          {answer ? (
            <div className="answer-box">
              <div className="ai-status-bar">
                <span className="status-badge neutral">{answer.risk_class}</span>
                <span className={`status-badge ${modelStatusClass(answer.model_status)}`}>
                  {modelStatusLabel(answer.model_status)}
                </span>
                {answer.mode ? <span className="status-badge neutral">模式：{answer.mode}</span> : null}
              </div>
              <p>{answer.answer}</p>
              {answer.citations.length ? (
                <div className="citation-grid">
                  {answer.citations.map((item) => (
                    <article className="citation-card" key={`${item.source_id}_${item.title}`}>
                      <header>
                        <strong>{item.title}</strong>
                        <span className="source-type">{item.source_type}</span>
                      </header>
                      <p>{item.snippet || "暂无片段摘要"}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <small>当前回答无可展示引用。</small>
              )}
              <p className="fine-print">{answer.disclaimer}</p>
            </div>
          ) : (
            <div className="empty-panel">还没有回答。可以从市场、标的详情或策略结果继续追问。</div>
          )}
        </article>
      </section>
    </div>
  );
}
