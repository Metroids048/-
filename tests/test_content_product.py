from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app


client = TestClient(app)


PROHIBITED_PHRASES = ("稳赚", "必中", "保证收益", "跟单赚钱", "买入建议", "卖出建议")


def assert_safe(payload):
    text = str(payload)
    for phrase in PROHIBITED_PHRASES:
        assert phrase not in text


def test_content_home_explains_simulation_positioning_and_business_ladder():
    response = client.get("/api/content/home")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_name"] == "AI投资想法体检器"
    assert "看到热点想买" in payload["positioning"]
    assert "虚拟样本回放" in payload["hero_promise"]
    assert payload["primary_cta"] == "生成想法体检卡"
    assert "不接真实资金" in str(payload["compliance_boundary"])
    assert "不构成投资建议" in str(payload["compliance_boundary"])
    assert_safe(payload)


def test_fund_risk_card_uses_plain_language_and_source_trace():
    response = client.post(
        "/api/funds/risk-card",
        json={
            "symbol": "510300",
            "name": "沪深300ETF",
            "question": "我持有这个基金，现在还能不能拿？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "510300"
    assert payload["risk_level"] in {"观察", "谨慎", "高风险"}
    assert len(payload["evidence"]) >= 4
    assert payload["action_boundary"].startswith("这不是买卖建议")
    assert payload["source"]["source_name"] in {"内置样本数据", "AKShare"}
    assert_safe(payload)


def test_strategy_validator_remains_as_guided_helper():
    response = client.post(
        "/api/strategy/validate",
        json={
            "idea": "我想定投沪深300，遇到创业板反弹时加一点弹性仓位",
            "symbols": ["510300", "159915"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["card_title"] == "策略想法验证卡"
    assert payload["rules"][0].startswith("标的池使用")
    assert payload["backtest"]["sample_range"] == "2026-05-20 至 2026-06-05"
    assert len(payload["risk_counterexamples"]) >= 3
    assert payload["user_next_step"].startswith("确认规则")
    assert_safe(payload)


def test_knowledge_base_and_alpha_factory_hide_raw_alpha_expressions():
    knowledge = client.get("/api/knowledge").json()
    articles = client.get("/api/knowledge/articles").json()
    factory = client.get("/api/alpha/factory").json()

    assert len(knowledge["lessons"]) >= 4
    assert len(articles["items"]) >= 30
    assert articles["total"] >= 30
    assert len(articles["categories"]) == 6
    assert articles["items"][0]["slug"]
    assert articles["items"][0]["summary"]
    detail = client.get(f"/api/knowledge/articles/{articles['items'][0]['slug']}").json()
    assert detail["body"]
    assert "不构成投资建议" in detail["disclaimer"]
    assert factory["source_assets"]["novelty_signatures"] >= 0
    assert factory["content_ideas"][0]["audience"] == "策略玩家"
    assert "raw_expression" not in str(factory)
    assert "WorldQuant" not in factory["public_positioning"]
    assert "asset_summary" in factory
    assert "available" in factory["asset_summary"]
    assert "scanned_factors" in factory["asset_summary"]
    assert "health_alerts" in factory
    assert "factor_families" in factory
    assert "体检" in factory["public_positioning"] or "本地 Alpha" in factory["public_positioning"]
    assert_safe(knowledge)
    assert_safe(articles)
    assert_safe(factory)


def test_knowledge_articles_support_category_and_search_filters():
    all_items = client.get("/api/knowledge/articles").json()["items"]
    category_items = client.get("/api/knowledge/articles", params={"category": "compliance"}).json()["items"]
    search_items = client.get("/api/knowledge/articles", params={"q": "回测"}).json()["items"]

    assert len(category_items) >= 5
    assert all(item["category"] == "compliance" for item in category_items)
    assert len(search_items) >= 3
    assert any("回测" in item["title"] or "回测" in item["summary"] for item in search_items)
    assert len(all_items) >= 30


def test_business_validation_exposes_simulation_metrics_and_four_week_plan():
    response = client.get("/api/business/validation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["north_star_metric"] == "每周重复查看同一模拟策略的用户数"
    assert payload["mvp_metrics"]["strategy"]["backtest_completion_rate"] == ">= 35%"
    assert len(payload["four_week_plan"]) == 4
    assert payload["four_week_plan"][3]["goal"] == "付费验证"
    assert payload["kill_criteria"][0].startswith("4-6周")
    assert_safe(payload)
