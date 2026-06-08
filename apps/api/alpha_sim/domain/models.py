from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


STRATEGY_STATUSES = {"draft", "compiled", "backtested", "paper_running", "paused", "failed", "data_insufficient"}
SIMULATION_STATUSES = {"pending", "running", "paused", "stopped", "data_insufficient"}
QUALITY_STATUSES = {"ok", "delayed", "partial", "unavailable", "conflict", "stale", "not_configured"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrategyRecord(SQLModel, table=True):
    __tablename__ = "strategies"

    id: int | None = Field(default=None, primary_key=True)
    strategy_id: str = Field(index=True, unique=True)
    name: str
    source: str
    market: str = "CN_A_ETF"
    frequency: str = "1d"
    status: str = "draft"
    asset_universe: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    entry_rules: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    exit_rules: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    position_rule: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=lambda: {"type": "fixed_fraction", "max_single_position": 0.3},
    )
    risk_rule: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=lambda: {"max_drawdown_stop": 0.12, "requires_manual_review": True},
    )
    constraints: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=lambda: {"t_plus_1": True, "min_lot": 100, "fee_rate": 0.0003, "slippage_bps": 5},
    )
    tags: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    disclaimer_required: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class BacktestReportRecord(SQLModel, table=True):
    __tablename__ = "backtests"

    id: int | None = Field(default=None, primary_key=True)
    backtest_id: str = Field(index=True, unique=True)
    strategy_id: str = Field(index=True)
    status: str = "pending"
    sample_range: str = ""
    metrics: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    assumptions: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    trades: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    failure_conditions: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    overfit_warning: str = ""
    disclaimer: str = "虚拟资金模拟，仅用于策略研究，不构成投资建议。"
    created_at: datetime = Field(default_factory=utc_now)


class PaperAccountRecord(SQLModel, table=True):
    __tablename__ = "paper_accounts"

    id: int | None = Field(default=None, primary_key=True)
    account_id: str = Field(index=True, unique=True)
    strategy_id: str = Field(index=True)
    initial_cash: float = 100000
    cash: float = 100000
    equity: float = 100000
    positions: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    trades: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    equity_curve: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SimulationRunRecord(SQLModel, table=True):
    __tablename__ = "simulation_runs"

    id: int | None = Field(default=None, primary_key=True)
    simulation_id: str = Field(index=True, unique=True)
    strategy_id: str = Field(index=True)
    account_id: str = Field(index=True)
    status: str = "pending"
    running_days: int = 0
    last_updated_at: datetime | None = None
    risk_events: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    leaderboard_eligible: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class DataSourceRecord(SQLModel, table=True):
    __tablename__ = "data_sources"

    id: int | None = Field(default=None, primary_key=True)
    source_name: str = Field(index=True, unique=True)
    tier: str
    domains: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    status: str = "not_configured"
    last_synced_at: datetime | None = None
    rights_status: str
    display_policy: str = "展示来源、更新时间和质量状态。"
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeDocument(SQLModel, table=True):
    __tablename__ = "knowledge_documents"

    id: int | None = Field(default=None, primary_key=True)
    document_id: str = Field(index=True, unique=True)
    title: str
    category: str
    content: str
    source_type: str = "internal_doc"
    rights_status: str = "internal_only"
    embedding: str | None = Field(sa_column=Column(JSON), default=None)
    created_at: datetime = Field(default_factory=utc_now)


class AiQuestionRecord(SQLModel, table=True):
    __tablename__ = "ai_questions"

    id: int | None = Field(default=None, primary_key=True)
    question_id: str = Field(index=True, unique=True)
    question: str
    entry_point: str
    risk_class: str
    context: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    citations: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    feedback: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ComplianceAuditLog(SQLModel, table=True):
    __tablename__ = "compliance_audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    scene: str
    text: str
    allowed: bool
    blocked_terms: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    replacement_guidance: str
    created_at: datetime = Field(default_factory=utc_now)
