"""
P0 endpoints:
- GET /api/content/home
- POST /api/content/share-card

Legacy/P2 endpoints below are retained for future expansion.
They must not be called by app/static P0 homepage.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import AlertCreate, ContentHome, JournalCreate, ShareCardRequest, ShareCardResponse, WatchlistCreate
from app.services.knowledge_loader import (
    CATEGORY_LABELS,
    get_article_by_slug,
    load_knowledge_documents,
    search_articles,
)
from app.services.rag.pipeline import run_rag_query
from app.services.alerts import create_alert, list_alerts
from app.services.content_home import get_content_home
from app.services.legacy_content import (
    get_alpha_factory,
    get_business_validation,
    get_knowledge_base,
)
from app.services.share_content import generate_share_card
from app.services.data_sources import list_data_sources
from app.services.journal import create_journal, list_journal
from app.services.watchlist import create_watchlist_item, list_watchlist
from app.services.watchlist_scan import build_daily_review_narrative, scan_watchlist
from apps.api.alpha_sim.services.validation import ValidationReleaseService

router = APIRouter(tags=["content"])


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=2)
    top_k: int = Field(default=5, ge=1, le=10)
    generate: bool = True
    entry_point: str = "knowledge_page"
    context: dict[str, str] = Field(default_factory=dict)


@router.get("/api/content/home", response_model=ContentHome)
def content_home():
    return get_content_home()


@router.post("/api/content/share-card", response_model=ShareCardResponse)
def content_share_card(payload: ShareCardRequest):
    try:
        return generate_share_card(
            diagnosis_id=payload.diagnosis_id,
            platform=payload.platform,
            diagnosis=payload.diagnosis,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/knowledge")
def knowledge_base():
    return get_knowledge_base()


def _article_list_item(article) -> dict:
    return {
        "slug": article.slug,
        "title": article.title,
        "category": article.category,
        "category_label": article.category_label,
        "tags": article.tags,
        "summary": article.summary,
        "source_path": article.source_path,
    }


@router.get("/api/knowledge/articles")
def knowledge_articles(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    articles = search_articles(category=category, query=q)
    categories = [
        {"id": key, "label": label, "count": len([a for a in load_knowledge_documents() if a.category == key])}
        for key, label in CATEGORY_LABELS.items()
    ]
    return {
        "items": [_article_list_item(article) for article in articles],
        "total": len(articles),
        "categories": categories,
    }


@router.get("/api/knowledge/articles/{slug}")
def knowledge_article_detail(slug: str):
    article = get_article_by_slug(slug)
    if not article:
        raise HTTPException(status_code=404, detail=f"知识库文章不存在：{slug}")
    return {
        "slug": article.slug,
        "title": article.title,
        "category": article.category,
        "category_label": article.category_label,
        "tags": article.tags,
        "summary": article.summary,
        "body": article.body,
        "source_path": article.source_path,
        "disclaimer": "以上内容仅供策略研究与学习，不构成投资建议。",
    }


@router.post("/api/knowledge/query")
def knowledge_query(payload: KnowledgeQueryRequest):
    result = run_rag_query(
        question=payload.question,
        context=payload.context,
        entry_point=payload.entry_point,
        top_k=payload.top_k,
        generate=payload.generate,
    )
    return {
        "question": payload.question,
        "chunks": result.get("chunks", []),
        "answer": result.get("answer"),
        "model_status": result.get("model_status"),
        "mode": result.get("mode"),
    }


@router.get("/api/alpha/factory")
def alpha_factory():
    return get_alpha_factory()


@router.get("/api/business/validation")
def business_validation():
    return get_business_validation()


@router.get("/api/validation/release")
def validation_release():
    service = ValidationReleaseService()
    package = service.build_release_package()
    return {
        "strategy_cards": package.strategy_cards,
        "metrics": package.metrics,
        "forbidden_entitlements": package.forbidden_entitlements,
        "readiness": service.readiness_checklist(),
    }


@router.get("/api/data/sources")
def data_sources():
    return list_data_sources()


@router.post("/api/alerts")
def alerts_create(payload: AlertCreate):
    return create_alert(payload)


@router.get("/api/alerts")
def alerts_list():
    return list_alerts()


@router.post("/api/watchlist")
def watchlist_create(payload: WatchlistCreate):
    return create_watchlist_item(payload)


@router.get("/api/watchlist")
def watchlist_list():
    return list_watchlist()


@router.post("/api/watchlist/scan")
def watchlist_scan():
    return scan_watchlist()


@router.get("/api/review/daily")
def review_daily():
    return build_daily_review_narrative()


@router.post("/api/journal")
def journal_create(payload: JournalCreate):
    return create_journal(payload)


@router.get("/api/journal")
def journal_list():
    return list_journal()
