from fastapi import APIRouter

from app.models import AiAskRequest, ComplianceCheckRequest
from app.services.llm_gateway import get_ollama_model, is_ollama_available
from app.services.rag.embedder import is_embedding_ready
from app.services.ai_ask import ask_alpha
from app.services.safety import check_compliance

router = APIRouter(tags=["ai"])


@router.post("/api/ai/ask")
def ai_ask(payload: AiAskRequest):
    return ask_alpha(payload)


@router.post("/api/compliance/check")
def compliance_check(payload: ComplianceCheckRequest):
    return check_compliance(payload.text, payload.scene)


@router.get("/api/ai/status")
def ai_status():
    return {
        "ollama_online": is_ollama_available(),
        "embedding_ready": is_embedding_ready(),
        "model": get_ollama_model(),
    }
