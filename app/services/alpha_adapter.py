import csv
import json
import os
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_ALPHA_DIR = "C:/Users/Windows11/Desktop/alpha"


def get_alpha_dir() -> Path:
    return Path(os.environ.get("ALPHA_DATA_DIR", DEFAULT_ALPHA_DIR))


def clear_alpha_summary_cache() -> None:
    load_alpha_summary.cache_clear()


@lru_cache(maxsize=1)
def load_alpha_summary() -> dict[str, Any]:
    alpha_dir = get_alpha_dir()
    novelty_path = alpha_dir / "alpha_novelty_index.json"
    feedback_path = alpha_dir / "alpha_feedback_learning_summary.csv"

    novelty = {
        "version": "unavailable",
        "normalized_count": 0,
        "operator_skeleton_count": 0,
        "field_signature_count": 0,
        "structure_signature_count": 0,
    }
    if novelty_path.exists():
        try:
            raw = json.loads(novelty_path.read_text(encoding="utf-8"))
            novelty.update(
                {
                    "version": raw.get("version", "unknown"),
                    "normalized_count": raw.get("normalized_count", 0),
                    "operator_skeleton_count": raw.get("operator_skeleton_count", 0),
                    "field_signature_count": raw.get("field_signature_count", 0),
                    "structure_signature_count": raw.get("structure_signature_count", 0),
                }
            )
        except (OSError, json.JSONDecodeError):
            pass

    rows: list[dict[str, str]] = []
    if feedback_path.exists():
        try:
            with feedback_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except OSError:
            rows = []

    scored_rows = [
        row
        for row in rows
        if _safe_float(row.get("count")) > 0 and row.get("family") not in {"unknown", ""}
    ]
    pass_rates = [_safe_float(row.get("metric_gate_pass_rate")) for row in scored_rows[:50]]
    best_families = sorted(
        scored_rows,
        key=lambda row: (_safe_float(row.get("metric_gate_pass_rate")), _safe_float(row.get("count"))),
        reverse=True,
    )[:5]
    blocked_reasons: dict[str, int] = {}
    for row in scored_rows:
        reason = row.get("top_blocked_reason") or "unknown"
        blocked_reasons[reason] = blocked_reasons.get(reason, 0) + int(_safe_float(row.get("count"), 0))

    unique_families = {row.get("family", "unknown") for row in scored_rows}
    duplicate_risk_count = sum(
        count for reason, count in blocked_reasons.items() if "self_correlation" in reason.lower()
    )
    overfit_alerts = sum(
        count
        for reason, count in blocked_reasons.items()
        if any(term in reason.lower() for term in ("sharpe", "sample", "turnover", "fit"))
    )
    backtest_ready_count = sum(1 for row in scored_rows if _safe_float(row.get("metric_gate_pass_rate")) >= 0.3)
    scanned_factors = max(len(rows), novelty["normalized_count"])

    return {
        "available": novelty_path.exists() or feedback_path.exists(),
        "novelty": novelty,
        "feedback_rows": len(rows),
        "average_recent_pass_rate": round(mean(pass_rates), 4) if pass_rates else 0.0,
        "best_families": [
            {
                "family": row.get("family", "unknown"),
                "source": row.get("source", "unknown"),
                "window": row.get("window", ""),
                "neutralization": row.get("Neutralization", ""),
                "pass_rate": _safe_float(row.get("metric_gate_pass_rate")),
                "sample_count": int(_safe_float(row.get("count"), 0)),
            }
            for row in best_families
        ],
        "blocked_reasons": dict(sorted(blocked_reasons.items(), key=lambda item: item[1], reverse=True)[:6]),
        "asset_metrics": {
            "scanned_factors": scanned_factors,
            "factor_families": len(unique_families),
            "duplicate_risk_count": duplicate_risk_count,
            "overfit_alerts": overfit_alerts,
            "strategy_card_candidates": len(scored_rows) or novelty["normalized_count"],
            "backtest_ready_count": backtest_ready_count,
        },
    }


def _safe_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def strategy_family_tags(prompt: str) -> list[str]:
    lower = prompt.lower()
    tags = []
    if any(term in prompt for term in ("动量", "趋势", "均线", "突破")):
        tags.append("momentum")
    if any(term in prompt for term in ("回撤", "反弹", "均值", "网格")):
        tags.append("mean_reversion")
    if any(term in prompt for term in ("财报", "ROE", "质量", "估值", "红利")):
        tags.append("fundamental_quality")
    if any(term in prompt for term in ("成交", "流动", "放量", "缩量")):
        tags.append("liquidity")
    if any(term in prompt for term in ("波动", "回撤", "风控")):
        tags.append("volatility")
    if "alpha" in lower or "因子" in prompt:
        tags.append("alpha_inspired")
    return tags or ["hybrid"]


def alpha_diagnostics_for_prompt(prompt: str) -> dict[str, Any]:
    summary = load_alpha_summary()
    tags = strategy_family_tags(prompt)
    warnings = [
        "本地alpha资料只用于策略灵感、质量诊断和失败案例，不展示原始表达式。",
        "若策略换手过高、样本过短或与既有策略相似，应先进入模拟盘观察。",
    ]
    blocked = summary.get("blocked_reasons", {})
    if any("self_correlation" in reason for reason in blocked):
        warnings.append("本地alpha反馈显示自相关/相似性是常见风险，需要避免重复策略。")
    if any("sharpe" in reason for reason in blocked):
        warnings.append("本地alpha反馈显示风险调整收益不足是常见失败原因。")

    return {
        "source": "local_alpha",
        "available": summary["available"],
        "strategy_family_tags": tags,
        "novelty_version": summary["novelty"]["version"],
        "novelty_signatures": summary["novelty"]["normalized_count"],
        "operator_skeletons": summary["novelty"]["operator_skeleton_count"],
        "field_signatures": summary["novelty"]["field_signature_count"],
        "average_recent_pass_rate": summary["average_recent_pass_rate"],
        "best_families": summary["best_families"],
        "blocked_reasons": summary["blocked_reasons"],
        "warnings": warnings,
    }
