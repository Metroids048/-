def test_validation_seed_builds_ten_strategy_cards_and_metrics():
    from apps.api.alpha_sim.services.validation import ValidationReleaseService

    service = ValidationReleaseService()
    package = service.build_release_package()

    assert len(package.strategy_cards) == 10
    assert package.strategy_cards[0]["name"]
    assert package.metrics["strategy_create_rate"]["target"] == ">= 25%"
    assert package.metrics["simulation_join_rate"]["target"] == ">= 20%"
    assert package.metrics["same_strategy_revisit_rate"]["target"] == ">= 20%"
    assert "实时买卖信号" in package.forbidden_entitlements


def test_release_readiness_checks_cover_compliance_data_and_core_flow():
    from apps.api.alpha_sim.services.validation import ValidationReleaseService

    service = ValidationReleaseService()
    readiness = service.readiness_checklist()
    keys = {item["key"] for item in readiness}

    assert {"core_flow", "compliance_boundary", "data_traceability", "rag_refusal", "paper_trading_only"}.issubset(keys)
    assert all(item["status"] in {"ready", "needs_manual_review"} for item in readiness)

