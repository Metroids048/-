from sqlmodel import SQLModel, create_engine


def test_domain_models_define_persistent_tables():
    from apps.api.alpha_sim.domain.models import (
        AiQuestionRecord,
        BacktestReportRecord,
        ComplianceAuditLog,
        DataSourceRecord,
        KnowledgeDocument,
        PaperAccountRecord,
        SimulationRunRecord,
        StrategyRecord,
    )

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    table_names = set(SQLModel.metadata.tables)

    assert {
        StrategyRecord.__tablename__,
        BacktestReportRecord.__tablename__,
        PaperAccountRecord.__tablename__,
        SimulationRunRecord.__tablename__,
        DataSourceRecord.__tablename__,
        KnowledgeDocument.__tablename__,
        AiQuestionRecord.__tablename__,
        ComplianceAuditLog.__tablename__,
    }.issubset(table_names)


def test_strategy_and_data_source_defaults_match_product_boundaries():
    from apps.api.alpha_sim.domain.models import DataSourceRecord, StrategyRecord

    strategy = StrategyRecord(
        strategy_id="str_demo",
        name="宽基ETF回撤分批模拟策略",
        source="user_prompt",
        market="CN_A_ETF",
        asset_universe=["510300"],
        entry_rules=[{"type": "drawdown_from_20d_high", "value": 0.05}],
        exit_rules=[{"type": "rebound_from_entry", "value": 0.03}],
    )
    source = DataSourceRecord(
        source_name="AKShare",
        tier="P0_free",
        domains=["stock_bars", "fund", "index"],
        status="not_configured",
        rights_status="public_reference",
    )

    assert strategy.status == "draft"
    assert strategy.disclaimer_required is True
    assert strategy.constraints["t_plus_1"] is True
    assert source.display_policy == "展示来源、更新时间和质量状态。"

