from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)


def test_asset_research_report_returns_structured_sections():
    response = client.get("/api/assets/510300/research-report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "510300"
    assert payload["name"]
    assert len(payload["sections"]) >= 3
    assert payload["trend_view"]
    assert len(payload["model_signals"]) >= 3
    assert len(payload["citations"]) >= 2
    assert "不构成投资建议" in payload["disclaimer"]
