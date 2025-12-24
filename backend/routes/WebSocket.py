import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket.WebSocketService import websocket_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  """
  Handles a websocket connection endpoint for real-time communication.

  The function manages the websocket workflow, allowing clients to send and
  receive messages. It facilitates broadcasting messages to all connected
  clients or echoing messages back to the sending client. The connection
  remains open until the client disconnects, enabling continuous communication.

  This function uses the websocket_service module to handle connection
  management, sending messages, and client disconnection.

  :param websocket: An instance of WebSocket representing the client connection.
  :type websocket: WebSocket
  :return: None
  """
  await websocket_service.connect(websocket)
  try:
    await websocket_service.listen_for_messages_json(websocket)
  except WebSocketDisconnect:
    await websocket_service.disconnect(websocket)
    logger.info("Client disconnected")
