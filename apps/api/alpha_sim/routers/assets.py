from typing import Literal

from fastapi import APIRouter, Query

from app.models import AssetOverview, AssetSearchResponse, FundRiskCardRequest
from app.services.data_sources import (
    build_asset_overview,
    build_asset_risk_card,
    build_fund_risk_card,
    get_asset_announcements,
    get_asset_bars,
    get_asset_financials,
    get_asset_profile,
    search_assets,
)
from app.services.research_report import build_asset_research_report
from app.services.data_score import build_data_score_card

router = APIRouter(tags=["assets"])


@router.get("/api/assets/search", response_model=AssetSearchResponse)
def asset_search(q: str = "", limit: int = Query(default=10, ge=1, le=20)):
    return search_assets(q, limit)


@router.post("/api/funds/risk-card")
def fund_risk_card(payload: FundRiskCardRequest):
    return build_fund_risk_card(payload)


@router.get("/api/assets/{symbol}/risk-card")
def asset_risk_card(symbol: str, name: str = ""):
    return build_asset_risk_card(symbol, name)


@router.get("/api/assets/{symbol}/data-score")
def asset_data_score(symbol: str, name: str = ""):
    return build_data_score_card(symbol, name)


@router.get("/api/assets/{symbol}/profile")
def asset_profile(symbol: str):
    return get_asset_profile(symbol)


@router.get("/api/assets/{symbol}/overview", response_model=AssetOverview)
def asset_overview(symbol: str):
    return build_asset_overview(symbol)


@router.get("/api/assets/{symbol}/bars")
def asset_bars(
    symbol: str,
    interval: Literal["1d", "1w", "1m"] = Query(default="1d"),
    limit: int = Query(default=120, ge=1, le=1000),
):
    return get_asset_bars(symbol, interval=interval, limit=limit)


@router.get("/api/assets/{symbol}/financials")
def asset_financials(symbol: str):
    return get_asset_financials(symbol)


@router.get("/api/assets/{symbol}/announcements")
def asset_announcements(symbol: str):
    return get_asset_announcements(symbol)


@router.get("/api/assets/{symbol}/research-report")
def asset_research_report(symbol: str):
    return build_asset_research_report(symbol)
