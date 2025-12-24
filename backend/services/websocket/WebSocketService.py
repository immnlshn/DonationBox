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

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the pool.

        Args:
            websocket: The WebSocket connection to remove
        """
        with self._lock:
            self._connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self._connections)}")

    async def listen_for_messages(self, websocket: WebSocket, echo: bool = True, broadcast: bool = False):
        """
        Listen for incoming messages from a WebSocket client.
        This keeps the connection open and handles incoming messages.

        Args:
            websocket: The WebSocket connection to listen on
            echo: If True, echo messages back to the sender (default: True)
            broadcast: If True, broadcast messages to all clients (default: False)
        """
        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received message from client: {data}")

                if echo:
                    await self.send_message(websocket, f"Echo: {data}")

                if broadcast:
                    await self.broadcast_message(f"Broadcast: {data}")
        except Exception as e:
            logger.debug(f"Error listening for messages: {e}")
            raise

    async def listen_for_messages_json(
        self,
        websocket: WebSocket,
        message_handler: Optional[Callable[[WebSocket, Dict[str, Any]], Awaitable[None]]] = None,
        echo: bool = False,
        broadcast: bool = False
    ):
        """
        Listen for incoming JSON messages from a WebSocket client with custom handler.
        This keeps the connection open and handles incoming JSON messages.

        Args:
            websocket: The WebSocket connection to listen on
            message_handler: Optional async function to handle messages.
                           Signature: async def handler(websocket: WebSocket, data: Dict[str, Any])
            echo: If True, echo messages back to the sender (default: False)
            broadcast: If True, broadcast messages to all clients (default: False)

        Example:
            async def my_handler(ws: WebSocket, data: Dict[str, Any]):
                if data.get("type") == "ping":
                    await websocket_service.send_json(ws, {"type": "pong"})

            await websocket_service.listen_for_messages_json(websocket, my_handler)
        """
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received JSON from client: {data}")

                # Call custom handler if provided
                if message_handler:
                    await message_handler(websocket, data)

                if echo:
                    await self.send_json(websocket, {"echo": data})

                if broadcast:
                    await self.broadcast_json({"broadcast": data})
        except Exception as e:
            logger.debug(f"Error listening for JSON messages: {e}")
            raise

    async def send_message(self, websocket: WebSocket, message: str):
        """
        Send a message to a specific WebSocket client.

        Args:
            websocket: The WebSocket connection to send to
            message: The message to send
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            await self.disconnect(websocket)

    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Send JSON data to a specific WebSocket client.

        Args:
            websocket: The WebSocket connection to send to
            data: The data to send as JSON
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending JSON to client: {e}")
            await self.disconnect(websocket)

    async def broadcast_message(self, message: str):
        """
        Broadcast a text message to all connected clients.
        Thread-safe and can be called from different threads.

        Args:
            message: The message to broadcast
        """
        with self._lock:
            connections = self._connections.copy()

        if not connections:
            logger.debug("No WebSocket clients connected, skipping broadcast")
            return

        disconnected = set()
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            with self._lock:
                self._connections -= disconnected

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

    def get_connection_count(self) -> int:
        """
        Get the current number of connected clients.

        Returns:
            The number of connected clients
        """
        with self._lock:
            return len(self._connections)

    def broadcast_message_sync(self, message: str):
        """
        Synchronous wrapper for broadcasting messages from non-async contexts.
        Useful for calling from threads that don't have an event loop.

        Args:
            message: The message to broadcast
        """
        try:
            # Get the running event loop or create a new one
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.create_task(self.broadcast_message(message))
            else:
                # If no loop is running, run it
                loop.run_until_complete(self.broadcast_message(message))
        except RuntimeError:
            # No event loop in current thread, create a task in the main loop
            logger.warning("No event loop in current thread, attempting to schedule broadcast")
            # This requires getting the main event loop reference
            # For now, log a warning - the caller should use the async version
            logger.error("Cannot broadcast from non-async context without event loop")

    def broadcast_json_sync(self, data: Dict[str, Any]):
        """
        Synchronous wrapper for broadcasting JSON from non-async contexts.
        Useful for calling from threads that don't have an event loop.

        Args:
            data: The data to broadcast as JSON
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast_json(data))
            else:
                loop.run_until_complete(self.broadcast_json(data))
        except RuntimeError:
            logger.warning("No event loop in current thread, attempting to schedule broadcast")
            logger.error("Cannot broadcast from non-async context without event loop")


# Global WebSocket service instance
websocket_service = WebSocketService()

