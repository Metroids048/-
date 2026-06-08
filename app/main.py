from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    AiAskRequest,
    AlertCreate,
    BacktestRequest,
    ComplianceCheckRequest,
    FundRiskCardRequest,
    JournalCreate,
    SimulationCreateRequest,
    StrategyCompileRequest,
    StrategySpec,
    StrategyValidationRequest,
    WatchlistCreate,
)
from app.services.ai_ask import ask_alpha
from app.services.alerts import create_alert, list_alerts
from app.services.backtest import run_backtest, run_seeded_backtest
from app.services.content_home import get_content_home
from app.services.legacy_content import (
    get_alpha_factory,
    get_business_validation,
    get_knowledge_base,
    validate_strategy,
)
from app.services.data_sources import (
    build_asset_risk_card,
    build_fund_risk_card,
    get_asset_announcements,
    get_asset_bars,
    get_asset_financials,
    get_asset_profile,
    list_data_sources,
)
from app.services.journal import create_journal, list_journal
from app.services.market import get_market_industries, get_market_summary
from app.services.safety import check_compliance
from app.services.simulation import create_simulation, get_leaderboard, get_simulation, seed_demo_data
from app.services.strategy import compile_strategy
from app.services.strategy_cards import get_strategy_card
from app.services.watchlist import create_watchlist_item, list_watchlist


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app_: FastAPI):
    seed_demo_data()
    yield


app = FastAPI(title="投研智体工作台", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/market/summary")
def market_summary():
    return get_market_summary()


@app.get("/api/market/industries")
def market_industries():
    return get_market_industries()


@app.get("/api/content/home")
def content_home():
    return get_content_home()


@app.post("/api/funds/risk-card")
def fund_risk_card(payload: FundRiskCardRequest):
    return build_fund_risk_card(payload)


@app.get("/api/assets/{symbol}/risk-card")
def asset_risk_card(symbol: str, name: str = ""):
    return build_asset_risk_card(symbol, name)


@app.get("/api/assets/{symbol}/profile")
def asset_profile(symbol: str):
    return get_asset_profile(symbol)


@app.get("/api/assets/{symbol}/bars")
def asset_bars(
    symbol: str,
    interval: Literal["1d", "1w", "1m"] = Query(default="1d"),
    limit: int = Query(default=120, ge=1, le=1000),
):
    return get_asset_bars(symbol, interval=interval, limit=limit)


@app.get("/api/assets/{symbol}/financials")
def asset_financials(symbol: str):
    return get_asset_financials(symbol)


@app.get("/api/assets/{symbol}/announcements")
def asset_announcements(symbol: str):
    return get_asset_announcements(symbol)


@app.get("/api/data/sources")
def data_sources():
    return list_data_sources()


@app.post("/api/strategy/validate")
def strategy_validate(payload: StrategyValidationRequest):
    return validate_strategy(payload)


@app.get("/api/knowledge")
def knowledge_base():
    return get_knowledge_base()


@app.get("/api/alpha/factory")
def alpha_factory():
    return get_alpha_factory()


@app.get("/api/business/validation")
def business_validation():
    return get_business_validation()


@app.post("/api/strategy/compile")
def strategy_compile_legacy(payload: StrategyCompileRequest):
    return compile_strategy(payload)


@app.post("/api/strategies/compile")
def strategy_compile(payload: StrategyCompileRequest):
    return compile_strategy(payload)


@app.get("/api/strategies/{strategy_id}")
def strategy_detail(strategy_id: str):
    return get_strategy_card(strategy_id)


@app.post("/api/backtests")
def backtest(payload: BacktestRequest | StrategySpec):
    if isinstance(payload, StrategySpec):
        return run_seeded_backtest(payload)
    return run_backtest(payload)


@app.post("/api/simulations")
def simulations_create(payload: SimulationCreateRequest):
    return create_simulation(payload)


@app.get("/api/simulations/{simulation_id}")
def simulations_get(simulation_id: str):
    return get_simulation(simulation_id)


@app.get("/api/leaderboards")
def leaderboards(type: str = "stability", market: str = "CN_A_ETF"):
    return get_leaderboard(type)


@app.post("/api/ai/ask")
def ai_ask(payload: AiAskRequest):
    return ask_alpha(payload)


@app.post("/api/compliance/check")
def compliance_check(payload: ComplianceCheckRequest):
    return check_compliance(payload.text, payload.scene)


@app.post("/api/alerts")
def alerts_create(payload: AlertCreate):
    return create_alert(payload)


@app.get("/api/alerts")
def alerts_list():
    return list_alerts()


@app.post("/api/watchlist")
def watchlist_create(payload: WatchlistCreate):
    return create_watchlist_item(payload)


@app.get("/api/watchlist")
def watchlist_list():
    return list_watchlist()


@app.post("/api/journal")
def journal_create(payload: JournalCreate):
    return create_journal(payload)


@app.get("/api/journal")
def journal_list():
    return list_journal()
