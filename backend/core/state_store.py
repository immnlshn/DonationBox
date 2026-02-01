"""
StateStore - In-memory state management for temporary application state.

Thread-safe key-value store for storing temporary state like:
- Selected category for next donation
- Temporary user choices
- Session state

No persistence - data is lost on application restart.
"""
import logging
from typing import Any
from threading import RLock

logger = logging.getLogger(__name__)


class StateStore:
    """
    Thread-safe in-memory key-value store for temporary state.

    This is a simple store without persistence. State is lost on restart.
    Use this for temporary data that doesn't need to be saved to database.
    """

    def __init__(self):
        """Initialize the state store with an empty dictionary and lock."""
        self._store: dict[str, Any] = {}
        self._lock = RLock()  # Reentrant lock for thread safety
        logger.info("StateStore initialized")

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the store.

        Args:
            key: Key to set
            value: Value to store (any Python object)
        """
        with self._lock:
            self._store[key] = value
            logger.debug(f"StateStore: Set {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the store.

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Stored value or default
        """
        with self._lock:
            value = self._store.get(key, default)
            logger.debug(f"StateStore: Get {key} = {value}")
            return value

    def delete(self, key: str) -> bool:
        """
        Delete a key from the store.

        Args:
            key: Key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                logger.debug(f"StateStore: Deleted {key}")
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the store.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._store

    def clear(self) -> None:
        """Clear all data from the store."""
        with self._lock:
            self._store.clear()
            logger.info("StateStore: Cleared all data")

    def get_all(self) -> dict[str, Any]:
        """
        Get a copy of all data in the store.

        Returns:
            Dictionary copy of all stored data
        """
        with self._lock:
            return self._store.copy()

    def update(self, data: dict[str, Any]) -> None:
        """
        Update multiple keys at once.

        Args:
            data: Dictionary of key-value pairs to update
        """
        with self._lock:
            self._store.update(data)
            logger.debug(f"StateStore: Updated {len(data)} keys")

    def pop(self, key: str, default: Any = None) -> Any:
        """
        Get and remove a value from the store.

        Args:
            key: Key to pop
            default: Default value if key doesn't exist

        Returns:
            Stored value or default
        """
        with self._lock:
            value = self._store.pop(key, default)
            logger.debug(f"StateStore: Popped {key} = {value}")
            return value

    def __len__(self) -> int:
        """Return the number of items in the store."""
        with self._lock:
            return len(self._store)

    def __contains__(self, key: str) -> bool:
        """Check if key exists using 'in' operator."""
        return self.exists(key)
