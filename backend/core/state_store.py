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

    def increment_nested(self, key: str, nested_key: str, amount: int | float, timestamp_key: str = None) -> tuple[int | float, float]:
        """
        Atomically increment a nested numeric value and optionally update a timestamp.

        This is useful for race-condition-free counter increments where the state
        is stored as a dictionary with numeric and timestamp fields.

        Args:
            key: Top-level key in the store
            nested_key: Key within the nested dictionary to increment
            amount: Amount to add (can be int or float)
            timestamp_key: Optional key for timestamp field to update

        Returns:
            Tuple of (new_value, timestamp)

        Example:
            # Increment total_donation_cents["amount"] by 50 and update timestamp
            new_total, ts = state_store.increment_nested(
                "total_donation_cents", "amount", 50, "timestamp"
            )
        """
        import time
        with self._lock:
            # Get current nested dict or create new one
            current_dict = self._store.get(key, {})
            if not isinstance(current_dict, dict):
                current_dict = {}

            # Increment the nested value
            current_value = current_dict.get(nested_key, 0)
            new_value = current_value + amount
            current_dict[nested_key] = new_value

            # Update timestamp if requested
            current_timestamp = time.time()
            if timestamp_key:
                current_dict[timestamp_key] = current_timestamp

            # Store back
            self._store[key] = current_dict
            logger.debug(f"StateStore: Incremented {key}[{nested_key}] by {amount} to {new_value}")

            return new_value, current_timestamp

