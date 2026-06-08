"use client";

import { useCallback, useEffect, useState } from "react";

type HealthPayload = {
  status: string;
  service: string;
  version: string;
};

export function ApiStatus() {
  const startupCommand = "py -3 -m uvicorn apps.api.alpha_sim.main:app --reload --port 8000";
  const [online, setOnline] = useState<boolean | null>(null);
  const [wrongBackend, setWrongBackend] = useState(false);
  const [detail, setDetail] = useState("");
  const [copied, setCopied] = useState(false);

  const check = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/health", { cache: "no-store" });
      if (!response.ok) {
        setOnline(false);
        setWrongBackend(false);
        setDetail(`健康检查失败：HTTP ${response.status}`);
        return;
      }
      const payload = (await response.json()) as HealthPayload;
      const healthy = payload.status === "ok";
      const mismatch = healthy && payload.service !== "alpha-sim-api";
      setOnline(healthy);
      setWrongBackend(mismatch);
      setDetail(`${payload.service} v${payload.version}`);
    } catch (error) {
      setOnline(false);
      setWrongBackend(false);
      setDetail(error instanceof Error ? error.message : "后端不可达");
    }
  }, []);

  useEffect(() => {
    void check();
    const timer = window.setInterval(() => void check(), 30000);
    return () => window.clearInterval(timer);
  }, [check]);

  if (online === null) {
    return (
      <div className="api-status checking" role="status">
        <span>后端连接检测中…</span>
      </div>
    );
  }

  const showStartupHint = !online || wrongBackend;
  const statusClass = wrongBackend ? "offline" : online ? "online" : "offline";
  const statusText = wrongBackend ? "连接了错误后端" : online ? "后端在线" : "后端离线";

  async function handleCopyCommand() {
    try {
      await navigator.clipboard.writeText(startupCommand);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className={`api-status ${statusClass}`} role="status">
      <span>{statusText}</span>
      <small>{detail}</small>
      {wrongBackend ? (
        <small className="api-status-hint">健康检查通过，但当前服务不是 alpha-sim-api，请切换到正确后端。</small>
      ) : null}
      {!online || wrongBackend ? (
        <button type="button" onClick={() => void check()}>
          重连
        </button>
      ) : null}
      {showStartupHint ? (
        <div className="api-status-cmd">
          <code>{startupCommand}</code>
          <button type="button" onClick={() => void handleCopyCommand()}>
            {copied ? "已复制" : "复制命令"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
