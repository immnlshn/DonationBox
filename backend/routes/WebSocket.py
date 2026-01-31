import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from backend.services.dependencies import get_websocket_service
from backend.services.websocket.WebSocketService import WebSocketService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ws_service: WebSocketService = Depends(get_websocket_service)
):
    """
    WebSocket endpoint for real-time communication.

    Manages the WebSocket workflow, allowing clients to receive broadcast messages
    about donations and vote updates. The connection remains open until the client
    disconnects, enabling continuous communication.

    Args:
        websocket: WebSocket connection instance
        ws_service: Injected WebSocketService from container

    Returns:
        None
    """
    logger.info("Client connected")

    await ws_service.connect(websocket)
    try:
        await ws_service.listen_for_messages_json(websocket)
    except WebSocketDisconnect:
        ws_service.disconnect(websocket)
        logger.info("Client disconnected")

