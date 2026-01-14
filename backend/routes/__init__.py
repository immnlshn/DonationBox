from fastapi import APIRouter

from . import WebSocket
from . import HelloWorld
from . import Voting
from ..settings import settings

api_router = APIRouter()

api_router.include_router(WebSocket.router, tags=["websocket"])
api_router.include_router(HelloWorld.router, tags=["hello_world"])
api_router.include_router(Voting.router, tags=["voting"])

if settings.PIN_FACTORY == "mock":
    from . import DebugGPIO
    api_router.include_router(DebugGPIO.router, prefix="/debug", tags=["debug_gpio"])

__all__ = ["api_router"]
