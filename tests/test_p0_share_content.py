from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)
FORBIDDEN = ("稳赚", "必胜", "买入", "卖出", "目标价", "跟单", "带单", "荐股")


def test_share_card_contract():
    diagnose = client.post(
        "/api/ideas/diagnose",
        json={
            "idea": "我想追 AI ETF，因为最近放量上涨",
            "market": "A股",
            "risk_preference": "小白默认",
        },
    )
    assert diagnose.status_code == 200
    diagnosis = diagnose.json()
    idea_id = diagnosis["idea_id"]

    response = client.post(
        "/api/content/share-card",
        json={"diagnosis_id": idea_id, "platform": "xiaohongshu"},
    )
    assert response.status_code == 200
    payload = response.json()

    for field in ["titles", "body", "short_video_script", "disclaimer"]:
        assert field in payload

    assert isinstance(payload["titles"], list) and len(payload["titles"]) >= 2
    script = payload["short_video_script"]
    for field in ["hook", "body", "ending"]:
        assert field in script

    text = str(payload)
    for phrase in FORBIDDEN:
        assert phrase not in text
    assert "不构成投资建议" in payload["disclaimer"]


def test_share_card_falls_back_to_diagnosis_payload():
    diagnosis = {
        "idea_id": "idea_missing_999",
        "raw_idea": "机器人概念突破后还能追吗",
        "idea_type": "题材幻想型",
        "emotion_tag": "故事驱动",
        "diagnosis_summary": "这是一个题材驱动想法。",
        "replay_type": "demo_virtual_sample",
        "replay_note": "以下为虚拟/示例样本回放，非真实历史统计，不代表未来表现。",
        "historical_replay": {
            "similar_cases": 15,
            "median_case": "+2.1%",
            "worst_case": "-8.3%",
            "max_drawdown": "-12.0%",
        },
        "risk_flags": ["叙事一致性过高", "拥挤交易风险偏高"],
        "failure_cases": ["龙头分歧后板块快速降温"],
        "xiaobai_reminder": "你可以把这张体检卡当成一次情绪与逻辑复盘。",
        "diagnosis_basis": ["题材热度"],
        "diagnosis_lens": "题材想法需要关注兑现节奏。",
        "disclaimer": "不构成投资建议，不提供买卖建议，不接真实资金，不承诺收益。",
    }

    response = client.post(
        "/api/content/share-card",
        json={
            "diagnosis_id": "idea_missing_999",
            "platform": "xiaohongshu",
            "diagnosis": diagnosis,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["titles"]
    assert payload["body"]
    assert payload["short_video_script"]["hook"]
    assert "不构成投资建议" in payload["disclaimer"]
