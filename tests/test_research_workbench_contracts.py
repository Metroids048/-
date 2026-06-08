from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app


client = TestClient(app)


def test_asset_profile_bars_and_risk_card_form_the_research_flow():
    profile = client.get("/api/assets/510300/profile").json()
    bars = client.get("/api/assets/510300/bars").json()
    risk = client.get("/api/assets/510300/risk-card").json()

    assert profile["symbol"] == "510300"
    assert profile["asset_type"] == "ETF"
    assert profile["research_entrypoints"] == ["kline", "risk_card", "ask_ai", "strategy_lab"]
    assert profile["source"]["quality_status"] in {"ok", "partial", "conflict"}

    assert bars["symbol"] == "510300"
    assert bars["interval"] == "1d"
    assert len(bars["bars"]) >= 10
    assert {"date", "open", "high", "low", "close", "volume"} <= set(bars["bars"][0])
    assert bars["source"]["rights_status"] in {"internal_sample", "public_reference"}

    assert risk["symbol"] == "510300"
    assert risk["source"]["quality_status"] in {"ok", "partial", "conflict"}


def test_market_industries_are_available_for_the_market_workspace():
    response = client.get("/api/market/industries")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) >= 4
    assert payload["items"][0]["name"]
    assert payload["items"][0]["temperature"] in {"cool", "neutral", "warm", "hot"}
    assert payload["source"]["source_name"]


def test_watchlist_accepts_asset_research_items_without_trading_language():
    created = client.post(
        "/api/watchlist",
        json={"symbol": "510300", "note": "观察沪深300ETF的回撤和成交量变化", "source": "asset_detail"},
    )
    listed = client.get("/api/watchlist")

    assert created.status_code == 200
    assert created.json()["symbol"] == "510300"
    assert created.json()["status"] == "observing"
    assert "不构成投资建议" in created.json()["compliance_note"]

    assert listed.status_code == 200
    assert any(item["symbol"] == "510300" for item in listed.json()["items"])
