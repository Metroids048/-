from __future__ import annotations

from app.services.alpha_signal_adapter import get_lens
from app.services.compliance_guard import (
    DEFAULT_DISCLAIMER,
    sanitize_output_list,
    sanitize_output_payload,
    sanitize_output_text,
    scan_input_warnings,
)

DIAGNOSIS_STORE: dict[str, dict] = {}

REPLAY_TYPE = "demo_virtual_sample"
REPLAY_NOTE = "以下为虚拟/示例样本回放，非真实历史统计，不代表未来表现。"


def _build_id() -> str:
    return f"idea_{len(DIAGNOSIS_STORE) + 1:03d}"


def _profile_for_idea(raw_idea: str) -> tuple[str, str, str, list[str], list[str]]:
    idea = raw_idea.lower()
    if any(key in idea for key in ["追", "放量上涨", "热点", "拉升", "突破"]):
        return (
            "追涨型",
            "怕错过",
            "这是一个典型的热点追涨想法，主要风险是高位拥挤后回撤。",
            ["短线热度偏高", "追涨风险偏高", "回撤承受力要求较高"],
            ["放量后价格滞涨", "主题热度快速退潮", "市场整体风险偏好下降"],
        )
    if any(key in idea for key in ["抄底", "跌", "到底", "便宜", "反弹"]):
        return (
            "抄底型",
            "害怕踏空反弹",
            "这是一个下跌后抄底想法，主要风险是下跌趋势未结束。",
            ["趋势反转信号不足", "下跌中继风险偏高", "仓位管理要求较高"],
            ["下跌后短暂反弹再破低点", "行业景气度继续走弱", "市场流动性继续收缩"],
        )
    if any(key in idea for key in ["亏", "亏损", "回撤", "为什么又亏"]):
        return (
            "亏损复盘型",
            "懊悔与焦虑",
            "这是一次亏损复盘想法，重点是定位触发亏损的行为模式。",
            ["入场纪律不清晰", "止损与退出规则缺失", "情绪化决策痕迹明显"],
            ["追高后遇到题材退潮", "没有退出条件导致亏损扩大", "单一叙事被市场证伪"],
        )
    if any(key in idea for key in ["红利", "高股息", "分红", "银行"]):
        return (
            "高股息型",
            "求稳",
            "这是一个偏防守的收益想法，风险是把稳定误解为没有波动。",
            ["风格切换风险", "收益来源过于单一", "估值回落风险"],
            ["高分红阶段结束后估值回调", "利率环境变化造成风格切换", "集中度过高影响波动"],
        )
    if any(key in idea for key in ["防守", "避险", "黄金"]):
        return (
            "防守型",
            "风险规避",
            "这是一个防守型想法，风险在于市场风格反转时跑输风险资产。",
            ["收益弹性有限", "风格反转时相对收益下降", "过度防守可能错失修复窗口"],
            ["避险资产高位回落", "市场风险偏好回升", "单一防守资产波动放大"],
        )
    if any(key in idea for key in ["题材", "概念", "机器人", "低空"]):
        return (
            "题材幻想型",
            "故事驱动",
            "这是一个题材驱动想法，风险在于预期先行后资金退潮。",
            ["叙事一致性过高", "拥挤交易风险偏高", "兑现节奏不确定"],
            ["龙头分歧后板块快速降温", "资金切换导致流动性下降", "兑现不及预期触发补跌"],
        )
    return (
        "趋势观察型",
        "等待确认",
        "这是一个趋势观察想法，建议先确认信号再决定是否继续研究。",
        ["趋势确认不足", "信号噪声偏高", "执行纪律要求较高"],
        ["信号失真导致反向波动", "市场切换使趋势中断", "风险预算不足导致体验变差"],
    )


def _historical_replay(raw_idea: str) -> dict:
    seed = sum(ord(char) for char in raw_idea)
    similar_cases = 12 + seed % 17
    median_case = f"+{(seed % 29) / 10:.1f}%"
    worst_case = f"-{(seed % 95) / 10:.1f}%"
    max_drawdown = f"-{(10 + seed % 70) / 5:.1f}%"
    return {
        "similar_cases": similar_cases,
        "median_case": median_case,
        "worst_case": worst_case,
        "max_drawdown": max_drawdown,
    }


def _normalize_symbol(symbol: str | None) -> str | None:
    if not symbol:
        return None
    normalized = symbol.strip().upper()
    return normalized or None


def diagnose_idea(
    idea: str,
    market: str = "A股",
    risk_preference: str = "小白默认",
    symbol: str | None = None,
) -> dict:
    raw_idea = idea.strip()
    normalized_symbol = _normalize_symbol(symbol)
    warning = scan_input_warnings(raw_idea)
    idea_type, emotion_tag, summary, risk_flags, failure_cases = _profile_for_idea(raw_idea)
    replay = _historical_replay(raw_idea + market + risk_preference + (normalized_symbol or ""))
    lens = get_lens(idea_type)
    basis_labels = list(lens["basis_labels"])
    if normalized_symbol:
        basis_labels.append(f"标的代码上下文：{normalized_symbol}")
    idea_id = _build_id()

    payload: dict = {
        "idea_id": idea_id,
        "raw_idea": raw_idea,
        "symbol": normalized_symbol,
        "idea_type": sanitize_output_text(idea_type),
        "emotion_tag": sanitize_output_text(emotion_tag),
        "diagnosis_summary": sanitize_output_text(summary),
        "replay_type": REPLAY_TYPE,
        "replay_note": REPLAY_NOTE,
        "historical_replay": replay,
        "risk_flags": sanitize_output_list(risk_flags),
        "failure_cases": sanitize_output_list(failure_cases),
        "xiaobai_reminder": sanitize_output_text(
            "你可以把这张体检卡当成一次情绪与逻辑复盘，不要把情绪当判断。"
        ),
        "diagnosis_basis": sanitize_output_list(basis_labels),
        "diagnosis_lens": sanitize_output_text(lens["plain_language"]),
        "disclaimer": DEFAULT_DISCLAIMER,
    }
    if warning:
        payload["warning"] = warning

    payload = sanitize_output_payload(payload)
    payload["raw_idea"] = raw_idea
    payload["replay_type"] = REPLAY_TYPE
    DIAGNOSIS_STORE[idea_id] = payload
    return payload


def get_diagnosis(idea_id: str) -> dict | None:
    return DIAGNOSIS_STORE.get(idea_id)
