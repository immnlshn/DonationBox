from fastapi import APIRouter

from . import WebSocket
from . import HelloWorld
from . import Voting
from . import Debug

api_router = APIRouter()

api_router.include_router(WebSocket.router, tags=["websocket"])
api_router.include_router(HelloWorld.router, tags=["hello_world"])
api_router.include_router(Voting.router, prefix="/voting", tags=["voting"])
api_router.include_router(Debug.router, prefix="/debug", tags=["debug"])

__all__ = ["api_router"]
