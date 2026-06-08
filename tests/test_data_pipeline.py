def test_p0_data_registry_exposes_required_sources_with_quality_metadata():
    from apps.api.alpha_sim.providers.registry import build_default_registry

    registry = build_default_registry()
    statuses = registry.statuses()
    names = {item.source_name for item in statuses}

    assert {"AKShare", "efinance", "qstock", "BaoStock", "巨潮资讯/交易所公告", "监管公开信息"}.issubset(names)
    assert all(item.quality_status in {"ok", "not_configured", "delayed", "partial", "conflict", "stale"} for item in statuses)
    assert all(item.rights_status for item in statuses)


def test_market_provider_returns_traceable_daily_bars_and_calendar():
    from apps.api.alpha_sim.providers.registry import build_default_registry

    registry = build_default_registry()
    bars = registry.market.daily_bars("510300")
    calendar = registry.market.trading_calendar("2026-06")

    assert bars.symbol == "510300"
    assert bars.quality_status == "ok"
    assert bars.source.source_name == "AKShare"
    assert bars.bars[0]["date"] <= bars.bars[-1]["date"]
    assert calendar["market"] == "CN_A"
    assert "2026-06-05" in calendar["trading_days"]


def test_public_information_provider_returns_announcements_financials_and_regulatory_items():
    from apps.api.alpha_sim.providers.registry import build_default_registry

    registry = build_default_registry()
    financials = registry.public_info.financial_snapshot("600000")
    announcements = registry.public_info.announcements("600000")
    regulatory = registry.public_info.regulatory_items()

    assert financials.source.source_name in {"BaoStock", "Tushare Pro", "内置财报样本"}
    assert financials.quality_status == "ok"
    assert announcements.items[0]["source_url"].startswith("https://")
    assert announcements.items[0]["summary"].startswith("机器摘要")
    assert any("非投资建议" in item["title"] for item in regulatory)

