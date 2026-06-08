from apps.api.alpha_sim.routers.ai import router as ai_router
from apps.api.alpha_sim.routers.assets import router as assets_router
from apps.api.alpha_sim.routers.content import router as content_router
from apps.api.alpha_sim.routers.ideas import router as ideas_router
from apps.api.alpha_sim.routers.market import router as market_router
from apps.api.alpha_sim.routers.simulations import router as simulations_router
from apps.api.alpha_sim.routers.strategies import router as strategies_router

__all__ = [
    "ai_router",
    "assets_router",
    "content_router",
    "ideas_router",
    "market_router",
    "simulations_router",
    "strategies_router",
]
