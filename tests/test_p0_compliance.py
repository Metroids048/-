from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)
FORBIDDEN = ("稳赚", "必胜", "买入建议", "卖出建议", "目标价", "跟单", "带单")
OUTPUT_FIELDS = (
    "idea_type",
    "emotion_tag",
    "diagnosis_summary",
    "risk_flags",
    "failure_cases",
    "xiaobai_reminder",
    "disclaimer",
    "diagnosis_lens",
    "replay_note",
)


def test_compliance_guard_blocks_forbidden_words_in_output():
    response = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "这个票稳赚钱，我想现在买入跟单",
            "market": "A股",
            "risk_preference": "小白默认",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["raw_idea"] == "这个票稳赚钱，我想现在买入跟单"
    assert "warning" in payload

    output_text = " ".join(str(payload.get(field, "")) for field in OUTPUT_FIELDS)
    output_text += " " + " ".join(payload.get("risk_flags", []))
    output_text += " " + " ".join(payload.get("failure_cases", []))
    for phrase in FORBIDDEN:
        assert phrase not in output_text
    assert "不构成投资建议" in payload["disclaimer"]


def test_compliance_output_has_no_forbidden_terms():
    response = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "机器人概念突破后还能追吗",
            "market": "A股",
            "risk_preference": "小白默认",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    output_text = " ".join(str(payload.get(field, "")) for field in OUTPUT_FIELDS)
    output_text += " " + " ".join(payload.get("risk_flags", []))
    output_text += " " + " ".join(payload.get("failure_cases", []))
    for phrase in ("稳赚", "必胜", "目标价", "跟着买", "牛股", "荐股", "带单", "保收益", "无风险"):
        assert phrase not in output_text
