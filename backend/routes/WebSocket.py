import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket.WebSocketService import websocket_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.

    Manages the WebSocket workflow, allowing clients to receive broadcast messages
    about donations and vote updates. The connection remains open until the client
    disconnects, enabling continuous communication.

    Args:
        websocket: WebSocket connection instance

    Returns:
        None
    """
    logger.info("Client connected")

    await websocket_service.connect(websocket)
    try:
        await websocket_service.listen_for_messages_json(websocket)
    except WebSocketDisconnect:
        websocket_service.disconnect(websocket)
        logger.info("Client disconnected")


