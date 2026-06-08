from datetime import datetime, timezone
import json

from sqlmodel import select

from app.models import BacktestReport, SimulationRun, StrategySpec
from app.services.rag.embedder import embed_texts
from app.services.ai_ask import AI_QUESTION_LOGS
from apps.api.alpha_sim.database import get_session
from apps.api.alpha_sim.domain.models import (
    AiQuestionRecord,
    BacktestReportRecord,
    KnowledgeDocument,
    SimulationRunRecord,
    StrategyRecord,
)
from app.services.knowledge_loader import load_knowledge_documents


def _now() -> datetime:
    return datetime.now(timezone.utc)


def persist_strategy(strategy: StrategySpec) -> None:
    with get_session() as session:
        existing = session.exec(
            select(StrategyRecord).where(StrategyRecord.strategy_id == strategy.strategy_id)
        ).first()
        fields = {
            "name": strategy.name,
            "source": strategy.source,
            "market": strategy.market,
            "frequency": strategy.frequency,
            "status": "compiled",
            "asset_universe": strategy.asset_universe,
            "entry_rules": [rule.model_dump() for rule in strategy.entry_rules],
            "exit_rules": [rule.model_dump() for rule in strategy.exit_rules],
            "position_rule": strategy.position_rule,
            "risk_rule": strategy.risk_rule,
            "constraints": strategy.constraints,
            "tags": strategy.tags,
            "updated_at": _now(),
        }
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            session.add(existing)
        else:
            session.add(StrategyRecord(strategy_id=strategy.strategy_id, **fields))
        session.commit()


def persist_backtest(report: BacktestReport) -> None:
    with get_session() as session:
        existing = session.exec(
            select(BacktestReportRecord).where(BacktestReportRecord.backtest_id == report.backtest_id)
        ).first()
        fields = {
            "strategy_id": report.strategy_id,
            "status": report.status,
            "sample_range": report.sample_range,
            "metrics": report.metrics,
            "assumptions": report.assumptions,
            "trades": [trade.model_dump() for trade in report.trades],
            "failure_conditions": report.failure_conditions,
            "overfit_warning": report.overfit_warning,
            "disclaimer": report.disclaimer,
        }
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            session.add(existing)
        else:
            session.add(BacktestReportRecord(backtest_id=report.backtest_id, **fields))
        session.commit()


def persist_simulation(run: SimulationRun) -> None:
    with get_session() as session:
        existing = session.exec(
            select(SimulationRunRecord).where(SimulationRunRecord.simulation_id == run.simulation_id)
        ).first()
        fields = {
            "strategy_id": run.strategy_id,
            "account_id": run.account_id,
            "status": run.status,
            "running_days": run.running_days,
            "last_updated_at": _now(),
            "risk_events": run.risk_events,
            "leaderboard_eligible": run.leaderboard_eligible,
        }
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            session.add(existing)
        else:
            session.add(SimulationRunRecord(simulation_id=run.simulation_id, **fields))
        session.commit()


def persist_ai_question(question: str, entry_point: str, risk_class: str, context: str) -> None:
    with get_session() as session:
        question_id = f"aq_{len(AI_QUESTION_LOGS):04d}"
        session.add(
            AiQuestionRecord(
                question_id=question_id,
                question=question,
                entry_point=entry_point,
                risk_class=risk_class,
                context={"raw": context},
            )
        )
        session.commit()


def seed_knowledge_documents() -> None:
    articles = load_knowledge_documents()
    if not articles:
        return

    with get_session() as session:
        existing = list(session.exec(select(KnowledgeDocument)).all())
        expected_ids = {article.document_id for article in articles}
        existing_ids = {doc.document_id for doc in existing}
        if existing_ids == expected_ids and len(existing) >= 30:
            return

        for doc in existing:
            session.delete(doc)
        session.commit()

        contents = [article.embedding_text for article in articles]
        vectors = embed_texts(contents)
        for index, article in enumerate(articles):
            embedding_payload = None
            if vectors and index < len(vectors):
                embedding_payload = json.dumps(vectors[index], ensure_ascii=False)
            session.add(
                KnowledgeDocument(
                    document_id=article.document_id,
                    title=article.title,
                    category=article.category,
                    content=article.embedding_text,
                    source_type="internal_doc",
                    rights_status="internal_only",
                    embedding=embedding_payload,
                )
            )
        session.commit()


def sync_runtime_state() -> None:
    from app.services import simulation as sim_module

    for strategy in sim_module.STRATEGIES.values():
        persist_strategy(strategy)
    for report in sim_module.BACKTESTS.values():
        persist_backtest(report)
    for run in sim_module.SIMULATIONS.values():
        persist_simulation(run)


def list_persisted_strategies(limit: int = 10) -> list[StrategyRecord]:
    with get_session() as session:
        return list(session.exec(select(StrategyRecord).limit(limit)).all())
