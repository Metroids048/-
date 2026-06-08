from app.models import (
    AlphaAssetSummary,
    AlphaFactorFamily,
    AlphaFactory,
    AlphaHealthAlert,
    BusinessValidation,
    KnowledgeBase,
    KnowledgeLesson,
    RevenueTier,
    StrategyValidationCard,
    StrategyValidationRequest,
)
from app.services.alpha_adapter import load_alpha_summary
from app.services.safety import compliance_note


def _pricing() -> list[RevenueTier]:
    return [
        RevenueTier(name="Free", price="¥0", user_value="1个策略、有限回测、7天观察摘要。"),
        RevenueTier(name="Inner Test", price="¥19.9/7天", user_value="更多策略、完整复盘报告预览、更多观察档案。"),
        RevenueTier(name="Standard", price="¥69/月候选", user_value="更多模拟账户、策略周报、风控诊断。"),
    ]


def validate_strategy(request: StrategyValidationRequest) -> StrategyValidationCard:
    symbols = request.symbols or ["510300", "159915"]
    return StrategyValidationCard(
        card_title="策略想法验证卡",
        user_idea=request.idea,
        rules=[
            f"标的池使用{', '.join(symbols)}，默认按日线盘后样本验证。",
            "先把自然语言想法转成入场、退出、仓位和风控规则。",
            "规则通过回测后才能加入虚拟模拟盘。",
            "连续触发风险反例时暂停策略并进入复盘。",
        ],
        backtest={
            "sample_range": "2026-05-20 至 2026-06-05",
            "annualized_return": "样本演示",
            "max_drawdown": "由回测实验室计算",
            "validation_count": 1,
            "interpretation": "该卡片用于解释验证流程，正式指标以回测报告为准。",
        },
        risk_counterexamples=[
            "样本期太短可能造成过拟合。",
            "回测好不代表模拟盘持续有效。",
            "真实市场中的停牌、涨跌停和流动性会影响执行。",
        ],
        user_next_step="确认规则后运行回测，再决定是否加入虚拟模拟盘。",
        compliance_note=compliance_note(),
    )


def get_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        lessons=[
            KnowledgeLesson(
                term="回测",
                plain_explanation="把策略规则放到历史样本里重跑一遍，观察它曾经如何表现。",
                why_it_matters="它只能证明样本内发生过什么，不能承诺未来结果。",
                example="同一个沪深300策略在趋势行情和震荡行情中的表现可能完全不同。",
            ),
            KnowledgeLesson(
                term="模拟盘",
                plain_explanation="用虚拟资金在持续更新的数据里运行策略。",
                why_it_matters="模拟盘比一次性回测更能暴露策略是否稳定，但仍不等于真实交易。",
                example="策略加入模拟盘后会记录虚拟持仓、虚拟成交和权益曲线。",
            ),
            KnowledgeLesson(
                term="最大回撤",
                plain_explanation="从账户高点跌到低点的最大幅度。",
                why_it_matters="普通用户往往高估自己承受亏损的能力，回撤能提前暴露心理压力。",
                example="权益从10万元跌到9.4万元，最大回撤约为-6%。",
            ),
            KnowledgeLesson(
                term="过拟合",
                plain_explanation="策略把历史样本记得太熟，看起来聪明，换个市场环境就失效。",
                why_it_matters="AI生成策略尤其容易出现看似复杂但不可持续的规则。",
                example="只在某几天刚好赚钱的参数，不一定能在模拟盘继续有效。",
            ),
        ]
    )


def _build_health_alerts(summary: dict) -> list[AlphaHealthAlert]:
    alerts: list[AlphaHealthAlert] = []
    metrics = summary.get("asset_metrics", {})
    blocked = summary.get("blocked_reasons", {})

    if not summary.get("available"):
        alerts.append(
            AlphaHealthAlert(
                level="info",
                title="本地 Alpha 目录未接入",
                detail="设置 ALPHA_DATA_DIR 环境变量后可扫描因子族、过拟合警报与策略候选。",
            )
        )
        return alerts

    if metrics.get("duplicate_risk_count", 0) > 0:
        alerts.append(
            AlphaHealthAlert(
                level="caution",
                title="存在自相关/相似因子风险",
                detail=f"检测到 {metrics['duplicate_risk_count']} 条相似性相关记录，建议优先去重后再进入回测观察。",
            )
        )
    if metrics.get("overfit_alerts", 0) > 0:
        alerts.append(
            AlphaHealthAlert(
                level="warning",
                title="疑似过拟合因子需复核",
                detail=f"有 {metrics['overfit_alerts']} 条记录触发样本/收益质量警报，不建议直接进入模拟盘。",
            )
        )
    if metrics.get("backtest_ready_count", 0) > 0:
        alerts.append(
            AlphaHealthAlert(
                level="info",
                title="可进入回测观察的因子族",
                detail=f"当前有 {metrics['backtest_ready_count']} 个因子族通过基础质量门槛，建议生成策略卡后回测。",
            )
        )
    for reason, count in list(blocked.items())[:2]:
        if count > 0 and "self_correlation" not in reason.lower():
            alerts.append(
                AlphaHealthAlert(
                    level="caution",
                    title=f"常见阻断：{reason}",
                    detail=f"本地反馈记录 {count} 次，进入模拟盘前请核对策略规则与样本区间。",
                )
            )
    return alerts[:4]


def get_alpha_factory() -> AlphaFactory:
    summary = load_alpha_summary()
    novelty = summary["novelty"]
    metrics = summary.get("asset_metrics", {})
    asset_summary = AlphaAssetSummary(
        available=summary["available"],
        scanned_factors=metrics.get("scanned_factors", 0),
        factor_families=metrics.get("factor_families", 0),
        duplicate_risk_count=metrics.get("duplicate_risk_count", 0),
        overfit_alerts=metrics.get("overfit_alerts", 0),
        strategy_card_candidates=metrics.get("strategy_card_candidates", 0),
        backtest_ready_count=metrics.get("backtest_ready_count", 0),
    )
    factor_families = [
        AlphaFactorFamily(
            family=item["family"],
            pass_rate=item["pass_rate"],
            sample_count=item["sample_count"],
            source=item.get("source", "unknown"),
        )
        for item in summary.get("best_families", [])
    ]
    return AlphaFactory(
        public_positioning="本地 Alpha 策略体检台：把已有因子和策略想法整理成可回测、可观察、可复盘的策略档案。",
        source_assets={
            "pipeline_version": novelty["version"],
            "novelty_signatures": novelty["normalized_count"],
            "operator_skeletons": novelty["operator_skeleton_count"],
            "field_signatures": novelty["field_signature_count"],
            "feedback_rows": summary["feedback_rows"],
        },
        asset_summary=asset_summary,
        health_alerts=_build_health_alerts(summary),
        factor_families=factor_families,
        content_ideas=[
            {"title": "为什么一个高收益回测可能进不了稳定性榜？", "audience": "策略玩家", "format": "失败案例"},
            {"title": "把一句ETF想法变成可验证规则", "audience": "A股/ETF用户", "format": "短视频脚本"},
            {"title": "自相关和过拟合为什么会让AI策略失效？", "audience": "量化初学者", "format": "知识卡"},
        ],
        internal_tools=["策略灵感库", "因子族标签", "过拟合警报", "失败案例库", "Alpha质量评分"],
    )


def get_business_validation() -> BusinessValidation:
    return BusinessValidation(
        north_star_metric="每周重复查看同一模拟策略的用户数",
        mvp_metrics={
            "strategy": {
                "strategy_create_rate": ">= 25%",
                "backtest_completion_rate": ">= 35%",
                "simulation_join_rate": ">= 20%",
            },
            "engagement": {
                "same_strategy_revisit_rate": ">= 20%",
                "ai_question_count": "每周>=50条",
                "leaderboard_view_rate": ">= 30%",
            },
            "business": {
                "trial_payment_rate": ">= 2%",
                "strategy_capacity_upgrade_reason": "能被用户主动提及",
                "refund_reason_tracking": "必须记录",
            },
        },
        four_week_plan=[
            {"week": "第1周", "goal": "公开模拟策略实验", "output": "10张策略卡、榜单样本、短视频脚本。"},
            {"week": "第2周", "goal": "上线MVP闭环", "output": "创建策略、回测、模拟盘、榜单、问问Alpha。"},
            {"week": "第3周", "goal": "渠道验证", "output": "抖音/小红书/公众号同步投放并收集问题。"},
            {"week": "第4周", "goal": "付费验证", "output": "开放¥19.9/7天或¥69/月内测。"},
        ],
        pricing=_pricing(),
        kill_criteria=[
            "4-6周内没有同策略复访，暂停复杂系统开发。",
            "用户只问买什么而不接受模拟验证，说明合规和商业错配。",
            "策略创建率和加入模拟盘率都低于预期时，优先重做入口而不是堆数据源。",
        ],
    )
