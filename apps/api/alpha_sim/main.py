from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.simulation import seed_demo_data
from apps.api.alpha_sim.database import init_db
from apps.api.alpha_sim.repositories.persistence import seed_knowledge_documents, sync_runtime_state
from apps.api.alpha_sim.routers import (
    ai_router,
    assets_router,
    content_router,
    ideas_router,
    market_router,
    simulations_router,
    strategies_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_knowledge_documents()
    seed_demo_data()
    sync_runtime_state()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI投资想法体检器 API",
        version="2.0.0",
        lifespan=lifespan,
    )

    @app.get("/api/v1/health")
    def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "alpha-sim-api",
            "version": app.version,
        }

    app.include_router(market_router)
    app.include_router(assets_router)
    app.include_router(strategies_router)
    app.include_router(simulations_router)
    app.include_router(ai_router)
    app.include_router(content_router)
    app.include_router(ideas_router)

    static_dir = Path(__file__).resolve().parents[3] / "app" / "static"

    @app.get("/")
    def index_page():
        return FileResponse(static_dir / "index.html")

    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app


app = create_app()
