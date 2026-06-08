FORBIDDEN_TERMS = (
    "赚钱",
    "稳赚",
    "必胜",
    "买入",
    "卖出",
    "目标价",
    "跟着买",
    "牛股",
    "荐股",
    "跟单",
    "带单",
    "翻倍",
    "无风险",
    "保收益",
)

OUTPUT_REPLACEMENTS = {
    "赚钱": "做想法复盘",
    "稳赚": "历史样本表现",
    "必胜": "需要继续验证",
    "买入": "继续观察",
    "卖出": "风险复盘",
    "目标价": "观察区间",
    "跟着买": "做独立判断",
    "牛股": "热点标的",
    "荐股": "想法体检",
    "跟单": "风险复盘",
    "带单": "教育展示",
    "翻倍": "波动风险",
    "无风险": "存在不确定性",
    "保收益": "不承诺收益",
}

DEFAULT_DISCLAIMER = (
    "仅用于投资想法复盘、虚拟样本回放和内容生成，不构成投资建议。"
)

INPUT_WARNING = (
    "你的输入包含买卖建议或收益承诺类表达，系统只会用于想法复盘，不会生成操作建议。"
)


def blocked_terms_in_text(text: str) -> list[str]:
    return [term for term in FORBIDDEN_TERMS if term in text]


def scan_input_warnings(text: str) -> str | None:
    if blocked_terms_in_text(text):
        return INPUT_WARNING
    return None


def sanitize_output_text(text: str) -> str:
    cleaned = text
    for phrase, replacement in OUTPUT_REPLACEMENTS.items():
        cleaned = cleaned.replace(phrase, replacement)
    return cleaned


def sanitize_output_list(values: list[str]) -> list[str]:
    return [sanitize_output_text(value) for value in values]


def sanitize_output_payload(payload):
    if isinstance(payload, str):
        return sanitize_output_text(payload)
    if isinstance(payload, list):
        return [sanitize_output_payload(item) for item in payload]
    if isinstance(payload, dict):
        return {key: sanitize_output_payload(value) for key, value in payload.items()}
    return payload


# Backward-compatible aliases for existing imports
sanitize_text = sanitize_output_text
sanitize_list = sanitize_output_list
sanitize_payload = sanitize_output_payload
