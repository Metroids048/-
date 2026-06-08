from fastapi import APIRouter

from app.models import (
    IdeaDiagnoseRequest,
    IdeaDiagnosisCard,
    TrendingIdeasResponse,
)
from app.services.idea_diagnosis import diagnose_idea
from app.services.trending_ideas import list_trending_ideas

router = APIRouter(tags=["idea-diagnosis"])


@router.post("/api/ideas/diagnose", response_model=IdeaDiagnosisCard)
def ideas_diagnose(payload: IdeaDiagnoseRequest):
    return diagnose_idea(
        idea=payload.idea,
        market=payload.market,
        risk_preference=payload.risk_preference,
        symbol=payload.symbol,
    )


@router.get("/api/ideas/trending", response_model=TrendingIdeasResponse)
def ideas_trending():
    return list_trending_ideas()
