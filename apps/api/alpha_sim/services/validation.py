from pydantic import BaseModel

from app.services.simulation import SIMULATIONS, STRATEGIES, get_leaderboard


class ValidationReleasePackage(BaseModel):
    strategy_cards: list[dict[str, str | list[str]]]
    metrics: dict[str, dict[str, str]]
    forbidden_entitlements: list[str]


class ValidationReleaseService:
    def build_release_package(self) -> ValidationReleasePackage:
        leaderboard = get_leaderboard("stability")
        strategy_cards = []
        for item in leaderboard.items[:10]:
            strategy = STRATEGIES.get(item.strategy_id)
            strategy_cards.append(
                {
                    "name": item.name,
                    "logic": strategy.explanation if strategy else "来自真实模拟盘记录",
                    "risk_counterexamples": strategy.warnings if strategy else ["样本期过短", "回测不等于未来"],
                    "paper_return": f"{item.paper_return:.2%}",
                    "running_days": str(item.running_days),
                }
            )
        while len(strategy_cards) < 10:
            strategy_cards.append(
                {
                    "name": "待用户创建策略",
                    "logic": "通过策略实验室创建并加入模拟盘后自动生成种子卡。",
                    "risk_counterexamples": ["暂无运行记录"],
                }
            )

        metrics = {
            "strategy_create_rate": {"target": ">= 25%", "meaning": "进入策略工厂后提交想法的用户比例"},
            "backtest_completion_rate": {"target": ">= 35%", "meaning": "策略草稿进入回测的比例"},
            "simulation_join_rate": {"target": ">= 20%", "meaning": "回测后加入虚拟模拟盘的比例"},
            "same_strategy_revisit_rate": {"target": ">= 20%", "meaning": "用户重复查看同一模拟策略的比例"},
            "running_simulations": {"target": f"{len(SIMULATIONS)}", "meaning": "当前数据库/内存中的模拟盘数量"},
        }
        return ValidationReleasePackage(
            strategy_cards=strategy_cards,
            metrics=metrics,
            forbidden_entitlements=["实时买卖信号", "个股推荐", "当前持仓即时跟单", "策略作者收费带单", "自动下单"],
        )

    def readiness_checklist(self) -> list[dict[str, str]]:
        return [
            {"key": "core_flow", "label": "策略想法到回测再到虚拟模拟盘闭环", "status": "ready"},
            {"key": "compliance_boundary", "label": "全站不出现买卖建议、目标价、跟单和收益承诺", "status": "ready"},
            {"key": "data_traceability", "label": "行情、财报、公告和监管条目都有来源与质量状态", "status": "ready"},
            {"key": "rag_refusal", "label": "问问Alpha对高风险买卖问题规则拒答", "status": "ready"},
            {"key": "paper_trading_only", "label": "只做虚拟资金模拟，不接券商和真实资金", "status": "ready"},
            {"key": "legal_review", "label": "付费页、免责声明和商业化文案建议人工法务复核", "status": "needs_manual_review"},
        ]
