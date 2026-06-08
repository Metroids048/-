from fastapi.testclient import TestClient

from apps.api.alpha_sim.main import app


client = TestClient(app)


PROHIBITED_PHRASES = ("稳赚", "必中", "保证收益", "自动下单", "跟着买", "买入建议", "卖出建议", "赚钱榜", "跟买榜")


def assert_safe_copy(payload):
    text = str(payload)
    for phrase in PROHIBITED_PHRASES:
        assert phrase not in text


def compile_demo_strategy():
    response = client.post(
        "/api/strategies/compile",
        json={
            "prompt": "沪深300回撤5%分批观察，反弹后退出虚拟仓位",
            "market": "CN_A_ETF",
            "preferred_assets": ["510300"],
            "risk_level": "moderate",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_market_summary_returns_explainable_signal_cards():
    response = client.get("/api/market/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["market_date"]
    assert payload["risk_level"] in {"低", "中", "高"}
    assert len(payload["hot_etfs"]) >= 3
    assert len(payload["signal_cards"]) >= 2
    assert payload["signal_cards"][0]["evidence"]
    assert payload["signal_cards"][0]["risk_counterpoint"]
    assert payload.get("source", {}).get("source_name")
    assert payload.get("updated_at")
    brief = payload["pre_market_brief"]
    assert brief is not None
    assert brief["direction_label"]
    assert brief["action_mantra"]
    assert len(brief["context"]) >= 2
    assert brief["methodology_note"]
    assert_safe_copy(payload)


def test_market_indices_returns_major_index_cards():
    response = client.get("/api/market/indices")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 4
    names = {item["name"] for item in payload["items"]}
    assert {"上证指数", "沪深300", "创业板指", "科创50"} <= names
    first = payload["items"][0]
    assert first["latest_price"] > 0
    assert isinstance(first["change_pct"], float)
    assert len(first["sparkline"]) >= 10
    assert payload["source"]["source_name"]
    assert payload["updated_at"]
    assert_safe_copy(payload)


def test_market_heatmap_returns_sector_treemap_items():
    response = client.get("/api/market/heatmap")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) >= 8
    assert payload["items"][0]["name"]
    assert isinstance(payload["items"][0]["change_pct"], float)
    assert payload["board_type"] == "industry"
    assert payload["source"]["source_name"]
    assert payload["updated_at"]
    assert_safe_copy(payload)


def test_asset_data_score_card_returns_dimensions_and_patterns():
    response = client.get("/api/assets/510300/data-score")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "510300"
    assert len(payload["dimensions"]) == 4
    assert 0 <= payload["composite_score"] <= 100
    assert payload["tracking_condition"]
    assert "不构成买卖建议" in payload["disclaimer"]
    assert_safe_copy(payload)


def test_asset_search_and_overview_are_traceable_p05_context():
    search = client.get("/api/assets/search?q=510300")
    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["query"] == "510300"
    assert search_payload["items"]
    first = search_payload["items"][0]
    assert first["symbol"] == "510300"
    assert first["source"]["source_name"]
    assert first["source"]["fetched_at"]
    assert first["source"]["data_time"]
    assert first["source"]["quality_status"]
    assert first["source"]["rights_status"]
    assert "不构成投资建议" in first["disclaimer"]
    assert_safe_copy(search_payload)

    overview = client.get("/api/assets/510300/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["symbol"] == "510300"
    assert overview_payload["latest_price"] is not None
    assert overview_payload["source"]["source_name"]
    assert overview_payload["quality_status"] in {"ok", "delayed", "partial", "unavailable", "conflict", "stale", "not_configured"}
    assert overview_payload["suggested_next_steps"]
    assert "不构成投资建议" in overview_payload["disclaimer"]
    assert_safe_copy(overview_payload)

    unknown = client.get("/api/assets/NO_SUCH_SYMBOL/overview")
    assert unknown.status_code == 200
    unknown_payload = unknown.json()
    assert unknown_payload["symbol"] == "NO_SUCH_SYMBOL"
    assert unknown_payload["latest_price"] is None
    assert unknown_payload["change_pct"] is None
    assert unknown_payload["fallback_notice"]
    assert_safe_copy(unknown_payload)


def test_watchlist_scan_and_daily_review_endpoints():
    scan = client.post("/api/watchlist/scan")
    assert scan.status_code == 200
    scan_payload = scan.json()
    assert "portfolio_summary" in scan_payload
    assert "needs_review" in scan_payload
    assert scan_payload["disclaimer"]
    assert_safe_copy(scan_payload)

    review = client.get("/api/review/daily")
    assert review.status_code == 200
    review_payload = review.json()
    assert review_payload["market_date"]
    assert len(review_payload["sections"]) >= 2
    assert review_payload["tracking_condition"]
    assert_safe_copy(review_payload)


def test_strategy_compile_turns_plain_language_into_strategy_spec():
    payload = compile_demo_strategy()

    assert payload["name"] == "宽基ETF回撤分批模拟策略"
    assert payload["asset_universe"] == ["510300"]
    assert payload["entry_rules"][0]["type"] == "drawdown_from_20d_high"
    assert payload["constraints"]["t_plus_1"] is True
    assert "mean_reversion" in payload["tags"]
    assert payload["warnings"][0].startswith("虚拟资金模拟")
    assert "raw_expression" not in str(payload)
    assert_safe_copy(payload)


def test_strategy_card_returns_dossier_fields_for_review_preview():
    strategy = compile_demo_strategy()
    response = client.get(f"/api/strategies/{strategy['strategy_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"]["strategy_id"] == strategy["strategy_id"]
    assert payload["backtest"]["strategy_id"] == strategy["strategy_id"]
    assert "alpha_diagnostics" in payload
    assert "strategy_family_tags" in payload["alpha_diagnostics"]
    assert len(payload["failure_conditions"]) >= 3
    assert len(payload["risk_counterexamples"]) >= 2
    assert payload["backtest"]["overfit_warning"]
    assert "虚拟资金模拟" in payload["disclaimer"]
    assert_safe_copy(payload)


def test_backtest_returns_report_with_costs_and_failure_conditions():
    strategy = compile_demo_strategy()
    response = client.post(
        "/api/backtests",
        json={"strategy": strategy, "initial_cash": 100000, "fee_rate": 0.0003, "slippage_bps": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["strategy_id"] == strategy["strategy_id"]
    assert payload["metrics"]["trade_count"] >= 1
    assert "max_drawdown" in payload["metrics"]
    assert payload["assumptions"]["t_plus_1"] is True
    assert len(payload["failure_conditions"]) >= 3
    assert "历史" not in payload["disclaimer"]
    assert_safe_copy(payload)


def test_simulation_and_leaderboard_show_virtual_results_only():
    strategy = compile_demo_strategy()
    backtest = client.post("/api/backtests", json={"strategy": strategy}).json()
    simulation = client.post(
        "/api/simulations",
        json={"strategy_id": strategy["strategy_id"], "backtest_id": backtest["backtest_id"], "initial_cash": 100000},
    ).json()

    assert simulation["status"] == "running"
    assert simulation["account"]["equity"] > 0
    assert simulation["account"]["positions"][0]["symbol"] == "510300"
    assert "虚拟资金模拟" in simulation["disclaimer"]

    leaderboard = client.get("/api/leaderboards?type=stability").json()
    assert leaderboard["title"] == "稳定性榜"
    assert len(leaderboard["items"]) >= 1
    assert "虚拟资金模拟表现" in leaderboard["disclaimer"]
    assert_safe_copy(leaderboard)


def test_simulations_list_and_longevity_board_are_available():
    items_response = client.get("/api/simulations")
    assert items_response.status_code == 200
    payload = items_response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)
    assert payload["items"], "expected at least one running simulation"
    first = payload["items"][0]
    required_fields = {
        "simulation_id",
        "strategy_id",
        "name",
        "status",
        "paper_return",
        "max_drawdown",
        "running_days",
        "started_at",
    }
    assert required_fields.issubset(first.keys())
    assert first["status"] == "running"

    longevity = client.get("/api/leaderboards?type=longevity")
    assert longevity.status_code == 200
    board = longevity.json()
    assert board["leaderboard_type"] == "longevity"
    assert board["title"] == "长跑榜"


def test_data_sources_financials_and_announcements_are_traceable():
    sources = client.get("/api/data/sources").json()
    financials = client.get("/api/assets/600000/financials").json()
    announcements = client.get("/api/assets/600000/announcements").json()

    assert any(item["source_name"] == "AKShare" for item in sources["items"])
    assert any(item["status"] == "not_configured" for item in sources["items"])
    assert financials["source"]["source_name"] == "内置财报样本"
    assert financials["quality_status"] == "ok"
    assert announcements["items"][0]["source_url"].startswith("https://")
    assert "机器摘要" in announcements["items"][0]["summary"]


def test_ai_ask_blocks_high_risk_questions_and_cites_strategy_context():
    blocked = client.post(
        "/api/ai/ask",
        json={"question": "现在能买吗，跟哪个策略买？", "entry_point": "global", "context": {}},
    ).json()

    assert blocked["risk_class"] == "blocked_investment_advice"
    assert "不能回答" in blocked["answer"]
    assert blocked["citations"][0]["source_type"] == "compliance_rule"
    assert_safe_copy(blocked)

    strategy = compile_demo_strategy()
    answer = client.post(
        "/api/ai/ask",
        json={
            "question": "这个策略为什么回撤高？",
            "entry_point": "strategy_detail",
            "context": {"strategy_id": strategy["strategy_id"]},
        },
    ).json()
    assert answer["risk_class"] == "strategy_explanation"
    assert len(answer["citations"]) >= 2
    assert "最大回撤" in answer["answer"]
    assert_safe_copy(answer)
