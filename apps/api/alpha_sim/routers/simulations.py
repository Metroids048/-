from fastapi import APIRouter

from app.models import BacktestRequest, SimulationCreateRequest, StrategySpec
from app.services.backtest import run_backtest, run_seeded_backtest
from app.services.simulation import create_simulation, get_leaderboard, get_simulation, list_simulations

router = APIRouter(tags=["simulations"])


@router.post("/api/backtests")
def backtest(payload: BacktestRequest | StrategySpec):
    if isinstance(payload, StrategySpec):
        return run_seeded_backtest(payload)
    return run_backtest(payload)


@router.post("/api/simulations")
def simulations_create(payload: SimulationCreateRequest):
    return create_simulation(payload)


@router.get("/api/simulations")
def simulations_list():
    return list_simulations()


@router.get("/api/simulations/{simulation_id}")
def simulations_get(simulation_id: str):
    return get_simulation(simulation_id)


@router.get("/api/leaderboards")
def leaderboards(type: str = "stability", market: str = "CN_A_ETF"):
    return get_leaderboard(type)
