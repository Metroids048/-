from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)


def test_p0_service_smoke_all_endpoints_return_200():
    health = client.get("/api/v1/health")
    assert health.status_code == 200

    home = client.get("/api/content/home")
    assert home.status_code == 200

    trending = client.get("/api/ideas/trending")
    assert trending.status_code == 200

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

    share = client.post(
        "/api/content/share-card",
        json={
            "diagnosis_id": diagnosis["idea_id"],
            "platform": "xiaohongshu",
            "diagnosis": diagnosis,
        },
    )
    assert share.status_code == 200
