import hashlib

from app.models import SourceRef, StrategyCompileRequest, StrategyRule, StrategySpec
from app.services.alpha_adapter import alpha_diagnostics_for_prompt, strategy_family_tags
from app.services.safety import check_compliance, compliance_note, ensure_safe_copy


DEFAULT_ASSETS = ["510300", "159915", "512880"]


def _strategy_id(prompt: str, assets: list[str]) -> str:
    digest = hashlib.sha1((prompt + "|".join(assets)).encode("utf-8")).hexdigest()[:8]
    return f"str_{digest}"


def _assets_from_request(request: StrategyCompileRequest) -> list[str]:
    assets = request.preferred_assets or request.watchlist or DEFAULT_ASSETS
    return [asset.strip() for asset in assets if asset.strip()]


def _template_name(prompt: str) -> str:
    if "网格" in prompt:
        return "ETF网格观察模拟策略"
    if "红利" in prompt:
        return "红利防守模拟策略"
    if "黄金" in prompt or "债券" in prompt:
        return "黄金债券避险轮动策略"
    if "行业" in prompt or "半导体" in prompt or "证券" in prompt:
        return "行业ETF动量模拟策略"
    if "回撤" in prompt or "分批" in prompt:
        return "宽基ETF回撤分批模拟策略"
    if "alpha" in prompt.lower() or "因子" in prompt:
        return "本地Alpha启发模拟策略"
    return "ETF均线趋势模拟策略"


def compile_strategy(request: StrategyCompileRequest) -> StrategySpec:
    compliance = check_compliance(request.prompt, "strategy_compile")
    if not compliance.allowed:
        prompt = ensure_safe_copy(request.prompt)
        warnings = ["输入包含高风险买卖表达，已改写为虚拟策略观察规则。"]
    else:
        prompt = request.prompt
        warnings = []

    assets = _assets_from_request(request)
    tags = strategy_family_tags(prompt)
    diagnostics = alpha_diagnostics_for_prompt(prompt)
    risk_level = request.risk_level or request.risk_preference or "moderate"
    max_position = 0.2 if risk_level in {"conservative", "保守"} else 0.3
    if risk_level in {"aggressive", "进取"}:
        max_position = 0.35

    if "回撤" in prompt or "分批" in prompt:
        entry_rules = [
            StrategyRule(
                type="drawdown_from_20d_high",
                operator=">=",
                value=0.05,
                description="当标的从20日高点回撤达到5%时，触发虚拟分批观察。",
            )
        ]
        exit_rules = [
            StrategyRule(
                type="rebound_from_entry",
                operator=">=",
                value=0.03,
                description="当虚拟持仓较观察价反弹3%或跌破风控线时，触发退出观察。",
            )
        ]
    elif "网格" in prompt:
        entry_rules = [
            StrategyRule(type="grid_down_step", operator=">=", value=0.03, description="每下行3%触发一档虚拟网格观察。")
        ]
        exit_rules = [
            StrategyRule(type="grid_up_step", operator=">=", value=0.03, description="每上行3%触发一档虚拟网格退出观察。")
        ]
    else:
        entry_rules = [
            StrategyRule(type="ma_breakout", operator=">=", value="20d_ma", description="收盘价站上20日均线且成交额改善时触发关注信号。")
        ]
        exit_rules = [
            StrategyRule(type="ma_breakdown", operator="<", value="10d_ma", description="收盘价跌破10日均线或组合回撤超过阈值时触发退出观察。")
        ]

    warnings.extend(
        [
            compliance_note(),
            "策略仅为规则草稿，必须经过回测和虚拟模拟观察，不能直接用于实盘。",
            *diagnostics["warnings"][:2],
        ]
    )

    return StrategySpec(
        strategy_id=_strategy_id(prompt, assets),
        name=_template_name(prompt),
        source="local_alpha_inspired" if "alpha_inspired" in tags else "user_prompt",
        asset_universe=assets,
        market=request.market,
        frequency="1d",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        position_rule={"type": "fixed_fraction", "max_single_position": max_position, "max_total_position": min(max_position * 2, 0.7)},
        risk_rule={"max_drawdown_stop": 0.12, "pause_after_risk_events": 2, "requires_manual_review": True},
        constraints={"t_plus_1": True, "min_lot": 100, "fee_rate": 0.0003, "slippage_bps": 5},
        tags=tags,
        source_refs=[
            SourceRef(
                source_name="本地alpha研究素材",
                source_url=None,
                fetched_at="2026-06-07T09:00:00+08:00",
                data_time="2026-06-06",
                rights_status="internal_only",
            )
        ],
        explanation=ensure_safe_copy(f"系统已把想法拆成可回测的虚拟模拟规则：{prompt}"),
        warnings=warnings,
        compliance_note=compliance_note(),
    )


def compile_strategy_legacy(request: StrategyCompileRequest) -> StrategySpec:
    return compile_strategy(request)
