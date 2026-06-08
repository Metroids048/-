from typing import Any

from pydantic import BaseModel

from apps.api.alpha_sim.services.strategy_engine import BacktestReportV2, SimulationRunV2, StrategySpecV2


DISCLAIMER = "问问Alpha基于当前站内数据、结构化对象和知识库解释，不构成投资建议。"


HIGH_RISK_PATTERNS = (
    "能买吗",
    "可以买",
    "该不该买",
    "要不要买",
    "推荐",
    "跟哪个策略",
    "目标价",
    "会涨吗",
    "会跌吗",
    "抄底",
    "加仓",
    "清仓",
)


class AskAlphaAnswer(BaseModel):
    answer_id: str
    risk_class: str
    answer: str
    citations: list[dict[str, str | None]]
    suggested_actions: list[dict[str, str]]
    disclaimer: str = DISCLAIMER


class QuestionClassifier:
    def classify(self, question: str, entry_point: str) -> str:
        if any(pattern in question for pattern in HIGH_RISK_PATTERNS):
            return "blocked_investment_advice"
        if entry_point in {"strategy_detail", "backtest"} or any(term in question for term in ("策略", "回撤", "回测", "模拟")):
            return "strategy_explanation"
        return "knowledge_answer"


class AskAlphaService:
    def __init__(
        self,
        strategies: dict[str, StrategySpecV2] | None = None,
        backtests: dict[str, BacktestReportV2] | None = None,
        simulations: dict[str, SimulationRunV2] | None = None,
    ):
        self.strategies = strategies or {}
        self.backtests = backtests or {}
        self.simulations = simulations or {}
        self.classifier = QuestionClassifier()
        self.question_logs: list[dict[str, Any]] = []

    def _log(self, question: str, entry_point: str, risk_class: str, context: dict[str, str]) -> None:
        self.question_logs.append(
            {
                "question": question,
                "entry_point": entry_point,
                "risk_class": risk_class,
                "context": context,
            }
        )

    def ask(self, question: str, entry_point: str, context: dict[str, str]) -> AskAlphaAnswer:
        risk_class = self.classifier.classify(question, entry_point)
        self._log(question, entry_point, risk_class, context)
        answer_id = f"ans_{len(self.question_logs):03d}"

        if risk_class == "blocked_investment_advice":
            return AskAlphaAnswer(
                answer_id=answer_id,
                risk_class=risk_class,
                answer="我不能回答现在是否买入、卖出、加仓、清仓、跟随哪个策略或目标价是多少。可以帮你解释风险证据、把想法转成可回测规则，或查看虚拟模拟表现。",
                citations=[
                    {
                        "source_type": "compliance_rule",
                        "source_id": "cr_no_advice_001",
                        "title": "非投资建议边界",
                        "url": "/api/v1/compliance/check",
                    }
                ],
                suggested_actions=[
                    {"type": "create_strategy", "label": "把想法转成模拟策略"},
                    {"type": "view_risk_card", "label": "查看风险卡"},
                ],
            )

        strategy_id = context.get("strategy_id", "")
        strategy = self.strategies.get(strategy_id)
        backtest = self.backtests.get(strategy_id)
        simulation = self.simulations.get(strategy_id)
        if risk_class == "strategy_explanation" and strategy and backtest:
            max_drawdown = backtest.metrics.get("max_drawdown", 0)
            running_days = simulation.running_days if simulation else 0
            return AskAlphaAnswer(
                answer_id=answer_id,
                risk_class=risk_class,
                answer=(
                    f"这个策略是{strategy.name}，核心规则来自用户想法并经过结构化。"
                    f"当前样本回测最大回撤为{max_drawdown}，虚拟模拟运行{running_days}天。"
                    "如果你关注回撤，重点看震荡阶段是否反复触发、费用和滑点是否侵蚀表现，以及是否出现风控事件。"
                ),
                citations=[
                    {"source_type": "strategy_spec", "source_id": strategy.strategy_id, "title": strategy.name, "url": None},
                    {"source_type": "backtest_report", "source_id": backtest.backtest_id, "title": "回测报告", "url": None},
                ],
                suggested_actions=[
                    {"type": "view_backtest", "label": "查看回测详情"},
                    {"type": "view_simulation", "label": "查看模拟盘表现"},
                ],
            )

        return AskAlphaAnswer(
            answer_id=answer_id,
            risk_class="no_grounded_evidence",
            answer="暂无足够依据，不能生成确定解释。这个问题已记录为知识库、策略模板或数据源缺口。",
            citations=[],
            suggested_actions=[
                {"type": "view_knowledge", "label": "查看知识库"},
                {"type": "create_strategy", "label": "创建模拟策略"},
            ],
        )
