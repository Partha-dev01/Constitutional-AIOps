"""Constitutional AIOps - API route modules."""

from src.api.routes.actions import router as actions_router
from src.api.routes.chat import router as chat_router
from src.api.routes.health import router as health_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.tools import router as tools_router

__all__ = [
    "health_router",
    "chat_router",
    "incidents_router",
    "actions_router",
    "tools_router",
]
