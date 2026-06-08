from fastapi import APIRouter

from app.models import StrategyCompileRequest, StrategyValidationRequest
from app.services.legacy_content import validate_strategy
from app.services.strategy import compile_strategy
from app.services.strategy_cards import get_strategy_card

router = APIRouter(tags=["strategies"])


@router.post("/api/strategy/validate")
def strategy_validate(payload: StrategyValidationRequest):
    return validate_strategy(payload)


@router.post("/api/strategy/compile")
def strategy_compile_legacy(payload: StrategyCompileRequest):
    return compile_strategy(payload)


@router.post("/api/strategies/compile")
def strategy_compile(payload: StrategyCompileRequest):
    return compile_strategy(payload)


@router.get("/api/strategies/{strategy_id}")
def strategy_detail(strategy_id: str):
    return get_strategy_card(strategy_id)
