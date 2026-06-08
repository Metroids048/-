from __future__ import annotations

IDEA_TYPE_LENS: dict[str, dict] = {
    "追涨型": {
        "factor_family": "动量 / 拥挤度 / 量价确认",
        "risk_lens": ["高位放量后回撤", "主题拥挤", "趋势失效"],
        "plain_language": "这个想法本质上是在赌趋势继续，但最怕热点突然退潮。",
        "basis_labels": ["动量", "拥挤度", "回撤风险", "题材退潮风险"],
    },
    "抄底型": {
        "factor_family": "均值回归 / 下跌动能 / 支撑确认",
        "risk_lens": ["下跌中继", "趋势未反转", "流动性收缩"],
        "plain_language": "这个想法是在赌跌够了，但趋势往往比预期更久。",
        "basis_labels": ["下跌动能", "反转信号", "仓位管理", "流动性"],
    },
    "亏损复盘型": {
        "factor_family": "行为模式 / 入场纪律 / 退出规则",
        "risk_lens": ["情绪化决策", "止损缺失", "单一叙事依赖"],
        "plain_language": "重点不是找下一个机会，而是定位这次亏损的行为模式。",
        "basis_labels": ["入场纪律", "退出规则", "情绪管理", "风险预算"],
    },
    "高股息型": {
        "factor_family": "股息率 / 估值 / 风格稳定性",
        "risk_lens": ["风格切换", "估值回落", "收益来源单一"],
        "plain_language": "防守不等于没波动，高分红阶段也可能遇到估值回调。",
        "basis_labels": ["股息稳定性", "估值", "风格切换", "集中度"],
    },
    "防守型": {
        "factor_family": "避险因子 / 低波动 / 相关性",
        "risk_lens": ["风格反转", "相对收益下降", "过度防守"],
        "plain_language": "避险有效，但市场风格反转时可能跑输风险资产。",
        "basis_labels": ["避险属性", "波动率", "风格反转", "相对收益"],
    },
    "题材幻想型": {
        "factor_family": "叙事强度 / 拥挤交易 / 资金切换",
        "risk_lens": ["叙事退潮", "龙头分歧", "兑现不及预期"],
        "plain_language": "故事很吸引人，但资金退潮时回撤往往很快。",
        "basis_labels": ["叙事强度", "拥挤度", "资金切换", "兑现节奏"],
    },
    "趋势观察型": {
        "factor_family": "趋势确认 / 信号噪声 / 执行纪律",
        "risk_lens": ["信号失真", "趋势中断", "风险预算不足"],
        "plain_language": "先确认信号，再决定是否继续研究，不要急着行动。",
        "basis_labels": ["趋势确认", "信号质量", "执行纪律", "风险预算"],
    },
}

DEFAULT_LENS = {
    "factor_family": "多因子观察 / 风险预算",
    "risk_lens": ["信号不足", "执行纪律", "风险预算"],
    "plain_language": "这是一个需要进一步观察的投资想法。",
    "basis_labels": ["趋势确认", "风险预算", "执行纪律"],
}


def get_lens(idea_type: str) -> dict:
    lens = IDEA_TYPE_LENS.get(idea_type, DEFAULT_LENS)
    return {
        "factor_family": lens["factor_family"],
        "risk_lens": list(lens["risk_lens"]),
        "plain_language": lens["plain_language"],
        "basis_labels": list(lens["basis_labels"]),
    }
