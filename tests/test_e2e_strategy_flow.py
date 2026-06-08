from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app

client = TestClient(app)


def test_compile_backtest_simulation_leaderboard_end_to_end():
    compile_response = client.post(
        "/api/strategies/compile",
        json={
            "prompt": "沪深300回撤5%分批观察，反弹后退出虚拟仓位",
            "market": "CN_A_ETF",
            "preferred_assets": ["510300"],
            "risk_level": "moderate",
        },
    )
    assert compile_response.status_code == 200
    strategy = compile_response.json()
    assert strategy["asset_universe"] == ["510300"]

    backtest_response = client.post(
        "/api/backtests",
        json={"strategy": strategy, "initial_cash": 100000, "fee_rate": 0.0003, "slippage_bps": 5},
    )
    assert backtest_response.status_code == 200
    backtest = backtest_response.json()
    assert backtest["status"] == "completed"
    assert backtest["strategy_id"] == strategy["strategy_id"]

    simulation_response = client.post(
        "/api/simulations",
        json={
            "strategy_id": strategy["strategy_id"],
            "backtest_id": backtest["backtest_id"],
            "initial_cash": 100000,
            "visibility": "public_delayed",
        },
    )
    assert simulation_response.status_code == 200
    simulation = simulation_response.json()
    assert simulation["strategy_id"] == strategy["strategy_id"]

    leaderboard_response = client.get("/api/leaderboards?type=stability")
    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    assert leaderboard["leaderboard_type"] == "stability"
    assert len(leaderboard["items"]) >= 1

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"


def test_p0_home_content_contract_supports_static_frontend():
    response = client.get("/api/content/home")

    assert response.status_code == 200
    payload = response.json()
    for field in [
        "product_name",
        "positioning",
        "hero_promise",
        "primary_cta",
        "compliance_boundary",
    ]:
        assert field in payload

    assert payload["product_name"] == "AI投资想法体检器"
    assert "虚拟样本回放" in payload["hero_promise"]
    assert payload["primary_cta"] == "生成想法体检卡"
    assert "不接真实资金" in str(payload["compliance_boundary"])
    assert "不构成投资建议" in str(payload["compliance_boundary"])
