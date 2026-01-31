import logging
import asyncio
from typing import Set, Dict, Any, Callable, Optional, Awaitable
from fastapi import WebSocket
from threading import Lock

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    WebSocket service for managing connections and broadcasting messages.
    Thread-safe and can be called from different services/threads.
    """

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = Lock()

    async def connect(self, websocket: WebSocket):
        """
        Add a new WebSocket connection to the pool.

        Args:
            websocket: The WebSocket connection to add
        """
        await websocket.accept()
        with self._lock:
            self._connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self._connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the pool.

        Args:
            websocket: The WebSocket connection to remove
        """
        with self._lock:
            self._connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self._connections)}")

    async def listen_for_messages_json(
        self,
        websocket: WebSocket,
        message_handler: Optional[Callable[[WebSocket, Dict[str, Any]], Awaitable[None]]] = None,
    ):
        """
        Listen for incoming JSON messages from a WebSocket client with custom handler.
        This keeps the connection open and handles incoming JSON messages.

        Args:
            websocket: The WebSocket connection to listen on
            message_handler: Optional async function to handle messages.
                           Signature: async def handler(websocket: WebSocket, data: Dict[str, Any])

        Example:
            async def my_handler(ws: WebSocket, data: Dict[str, Any]):
                if data.get("type") == "ping":
                    await websocket_service.broadcast_json({"type": "pong"})

            await websocket_service.listen_for_messages_json(websocket, my_handler)
        """
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received JSON from client: {data}")

                # Call custom handler if provided
                if message_handler:
                    await message_handler(websocket, data)
        except Exception as e:
            logger.debug(f"Error listening for JSON messages: {e}")
            raise

    async def broadcast_json(self, data: Dict[str, Any]):
        """
        Broadcast JSON data to all connected clients.
        Thread-safe and can be called from different threads.

        Args:
            data: The data to broadcast as JSON
        """
        with self._lock:
            connections = self._connections.copy()

        if not connections:
            logger.debug("No WebSocket clients connected, skipping broadcast")
            return

        disconnected = set()
        for websocket in connections:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting JSON to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            with self._lock:
                self._connections -= disconnected

    def broadcast_json_sync(self, data: Dict[str, Any]):
        """
        Synchronous wrapper for broadcasting JSON from synchronous contexts.
        Schedules the broadcast as an asyncio task if event loop is running.
        Can be called from both sync and async contexts.

        Args:
            data: The data to broadcast as JSON
        """
        try:
            asyncio.get_running_loop()
            # We're in an async context - schedule the broadcast task
            # Store task reference to prevent premature garbage collection
            _ = asyncio.create_task(self.broadcast_json(data))
            logger.debug(f"Broadcast scheduled in event loop, {len(self._connections)} connections")
        except RuntimeError:
            # No running event loop - shouldn't happen in FastAPI but log it
            logger.warning("Cannot broadcast: No running event loop found")
        except Exception as e:
            logger.error(f"Error scheduling broadcast: {e}", exc_info=True)

    def get_connection_count(self) -> int:
        """
        Get the current number of connected clients.

        Returns:
            The number of connected clients
        """
        with self._lock:
            return len(self._connections)

    async def close_all_connections(self):
        """
        Close all WebSocket connections gracefully.
        Should be called during application shutdown.
        """
        with self._lock:
            connections = self._connections.copy()
            self._connections.clear()

        if not connections:
            logger.debug("No WebSocket connections to close")
            return

        logger.info(f"Closing {len(connections)} WebSocket connections...")
        for websocket in connections:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")

        logger.info("All WebSocket connections closed")

