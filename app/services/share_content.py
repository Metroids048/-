from app.services.compliance_guard import DEFAULT_DISCLAIMER, sanitize_output_payload, sanitize_output_text
from app.services.idea_diagnosis import get_diagnosis


def _build_titles(diagnosis: dict) -> list[str]:
    idea_type = diagnosis["idea_type"]
    return [
        sanitize_output_text("我让 AI 体检了这个热点想法"),
        sanitize_output_text("看到热点别急，先看风险反例"),
        sanitize_output_text(f"AI 判断这是{idea_type}，先做一次想法复盘"),
    ]


def _build_body(diagnosis: dict) -> str:
    replay = diagnosis["historical_replay"]
    return sanitize_output_text(
        f"今天我把一个投资想法丢进体检器，系统判定为{diagnosis['idea_type']}，"
        f"情绪标签是{diagnosis['emotion_tag']}。"
        f"以下为虚拟样本回放：类似场景约 {replay['similar_cases']} 次，"
        f"中位表现 {replay['median_case']}，最差样本 {replay['worst_case']}，"
        f"最大回撤 {replay['max_drawdown']}。"
        f"这不是操作建议，只是帮助我先做风险复盘。"
    )


def _resolve_diagnosis(
    diagnosis_id: str | None = None,
    diagnosis: dict | None = None,
) -> dict:
    if diagnosis_id:
        cached = get_diagnosis(diagnosis_id)
        if cached:
            return cached
    if diagnosis:
        return diagnosis
    raise KeyError("diagnosis not found: provide a valid diagnosis_id or diagnosis payload")


def generate_share_card(
    diagnosis_id: str | None = None,
    platform: str = "xiaohongshu",
    diagnosis: dict | None = None,
) -> dict:
    resolved = _resolve_diagnosis(diagnosis_id=diagnosis_id, diagnosis=diagnosis)

    hook = sanitize_output_text("今天这个热点，你是不是也想冲？我先做了个想法体检。")
    body = sanitize_output_text(
        f"AI 判断这是{resolved['idea_type']}，核心风险是："
        + "、".join(resolved["risk_flags"][:2])
        + "。以下为虚拟样本回放，非真实历史统计。"
    )
    ending = sanitize_output_text("这不是投资建议，只是一次投资想法复盘。")

    payload = {
        "titles": _build_titles(resolved),
        "body": _build_body(resolved),
        "short_video_script": {"hook": hook, "body": body, "ending": ending},
        "disclaimer": DEFAULT_DISCLAIMER,
        "platform": platform,
    }
    payload = sanitize_output_payload(payload)
    payload.pop("platform", None)
    return payload
