from fastapi import APIRouter

from app.services.market import (
    get_market_heatmap,
    get_market_indices,
    get_market_industries,
    get_market_summary,
)

router = APIRouter(tags=["market"])


@router.get("/api/market/summary")
def market_summary():
    return get_market_summary()


@router.get("/api/market/industries")
def market_industries():
    return get_market_industries()


@router.get("/api/market/indices")
def market_indices():
    return get_market_indices()


@router.get("/api/market/heatmap")
def market_heatmap():
    return get_market_heatmap()
