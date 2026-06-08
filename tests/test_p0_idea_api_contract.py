from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)


def test_idea_diagnosis_contract():
    response = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "我想追 AI ETF，因为最近放量上涨",
            "market": "A股",
            "risk_preference": "小白默认",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    for field in [
        "idea_id",
        "raw_idea",
        "idea_type",
        "emotion_tag",
        "diagnosis_summary",
        "replay_type",
        "replay_note",
        "historical_replay",
        "risk_flags",
        "failure_cases",
        "xiaobai_reminder",
        "diagnosis_basis",
        "diagnosis_lens",
        "disclaimer",
    ]:
        assert field in payload

    assert payload["replay_type"] == "demo_virtual_sample"
    assert payload["replay_note"] == "以下为虚拟/示例样本回放，非真实历史统计，不代表未来表现。"
    assert payload["raw_idea"] == "我想追 AI ETF，因为最近放量上涨"
    assert isinstance(payload["diagnosis_basis"], list)
    assert isinstance(payload["diagnosis_lens"], str)

    replay = payload["historical_replay"]
    for key in ["similar_cases", "median_case", "worst_case", "max_drawdown"]:
        assert key in replay

    assert isinstance(payload["risk_flags"], list) and payload["risk_flags"]
    assert isinstance(payload["failure_cases"], list) and payload["failure_cases"]
    assert "不构成投资建议" in payload["disclaimer"]


def test_short_chinese_idea_is_accepted():
    response = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "光模块",
            "market": "A股",
            "risk_preference": "小白默认",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["raw_idea"] == "光模块"
    assert payload["replay_type"] == "demo_virtual_sample"


def test_idea_diagnosis_accepts_optional_symbol_context():
    response = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "我想先看看沪深300ETF是不是又上头了",
            "market": "A股",
            "risk_preference": "小白默认",
            "symbol": "510300",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["raw_idea"] == "我想先看看沪深300ETF是不是又上头了"
    assert payload["symbol"] == "510300"
    assert payload["replay_type"] == "demo_virtual_sample"
    assert any("510300" in item for item in payload["diagnosis_basis"])
    assert "不构成投资建议" in payload["disclaimer"]


def test_ideas_trending_contract():
    response = client.get("/api/ideas/trending")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload and isinstance(payload["items"], list)
    assert "disclaimer" in payload
    assert "不构成投资建议" in payload["disclaimer"]
    assert payload["items"], "trending items should not be empty"

    item = payload["items"][0]
    for field in ["id", "title", "idea_type", "heat_score", "risk_score", "teaser"]:
        assert field in item
