from app.models import ComplianceCheckResponse


PROHIBITED_TERMS = (
    "买入",
    "卖出",
    "加仓",
    "清仓",
    "目标价",
    "稳赚",
    "必涨",
    "必中",
    "保证收益",
    "跟着买",
    "跟单",
    "抄底",
    "自动下单",
    "无脑",
)

REPLACEMENTS = {
    "买入": "触发策略观察规则",
    "卖出": "触发退出观察规则",
    "加仓": "调整虚拟仓位规则",
    "清仓": "降低虚拟风险暴露",
    "目标价": "观察区间",
    "稳赚": "历史样本表现",
    "必涨": "存在不确定性",
    "必中": "需要验证",
    "保证收益": "历史表现",
    "跟着买": "查看虚拟模拟表现",
    "跟单": "观察模拟策略",
    "抄底": "观察回撤修复",
    "自动下单": "人工确认",
    "无脑": "审慎参考",
}

DISCLAIMER = "虚拟资金模拟，仅用于策略研究、投研解释和学习复盘，不构成投资建议。"


def ensure_safe_copy(text: str) -> str:
    safe = text
    for phrase, replacement in REPLACEMENTS.items():
        safe = safe.replace(phrase, replacement)
    return safe


def compliance_note() -> str:
    return DISCLAIMER


def check_compliance(text: str, scene: str = "general") -> ComplianceCheckResponse:
    blocked = [term for term in PROHIBITED_TERMS if term in text]
    return ComplianceCheckResponse(
        allowed=not blocked,
        blocked_terms=blocked,
        replacement_guidance=(
            "请改写为策略规则、虚拟模拟表现、风险证据或观察状态，不输出实盘买卖建议。"
            if blocked
            else "当前文本未触发硬性合规拦截。"
        ),
    )


def is_high_risk_question(question: str) -> bool:
    high_risk_patterns = (
        "能买吗",
        "可以买",
        "该不该买",
        "要不要买",
        "推荐",
        "跟哪个策略",
        "目标价",
        "会涨吗",
        "会跌吗",
        "抄底",
        "加仓",
        "清仓",
    )
    return any(pattern in question for pattern in high_risk_patterns)
