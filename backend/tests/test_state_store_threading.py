"""
Test thread safety of StateStore increment_nested operation.
"""
import pytest
import threading
import time
from backend.core.state_store import StateStore


class TestStateStoreThreadSafety:
    """Test StateStore thread safety, especially increment_nested."""

    def test_increment_nested_basic(self):
        """Test basic increment_nested functionality."""
        store = StateStore()

        # First increment
        new_value, timestamp = store.increment_nested(
            "total_donation_cents",
            "amount",
            50,
            "timestamp"
        )

        assert new_value == 50
        assert timestamp > 0

        # Second increment
        new_value, timestamp2 = store.increment_nested(
            "total_donation_cents",
            "amount",
            30,
            "timestamp"
        )

        assert new_value == 80
        assert timestamp2 >= timestamp

    def test_increment_nested_concurrent(self):
        """Test that concurrent increments are atomic and don't lose updates."""
        store = StateStore()
        num_threads = 10
        increments_per_thread = 100
        increment_amount = 1

        def worker():
            """Worker thread that performs multiple increments."""
            for _ in range(increments_per_thread):
                store.increment_nested(
                    "total_donation_cents",
                    "amount",
                    increment_amount,
                    "timestamp"
                )

        # Start all threads
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check final value - should be exactly num_threads * increments_per_thread
        expected_total = num_threads * increments_per_thread * increment_amount
        final_data = store.get("total_donation_cents")

        assert final_data is not None
        assert final_data["amount"] == expected_total, \
            f"Expected {expected_total} but got {final_data['amount']} - race condition detected!"

    def test_increment_nested_with_floats(self):
        """Test increment_nested with float values (e.g., currency with decimals)."""
        store = StateStore()

        store.increment_nested("balance", "amount", 1.5)
        store.increment_nested("balance", "amount", 2.3)
        new_value, _ = store.increment_nested("balance", "amount", 0.7)

        # Use approximate comparison for floats
        assert abs(new_value - 4.5) < 0.001

    def test_increment_nested_creates_new_dict(self):
        """Test that increment_nested creates new nested dict if key doesn't exist."""
        store = StateStore()

        new_value, timestamp = store.increment_nested(
            "new_key",
            "amount",
            100,
            "timestamp"
        )

        assert new_value == 100
        data = store.get("new_key")
        assert data["amount"] == 100
        assert "timestamp" in data

    def test_increment_nested_without_timestamp(self):
        """Test increment_nested without timestamp update."""
        store = StateStore()

        new_value, timestamp = store.increment_nested(
            "counter",
            "value",
            10
        )

        assert new_value == 10
        assert timestamp > 0  # Timestamp still returned for consistency

        data = store.get("counter")
        assert "timestamp" not in data  # But not stored

    def test_increment_nested_race_condition_simulation(self):
        """
        Simulate the exact race condition scenario from the coin validator:
        Multiple rapid coin insertions should all be counted correctly.
        """
        store = StateStore()
        coin_values = [10, 20, 50, 100, 200]  # Different coin values in cents
        num_insertions = 20  # Total number of coin insertions

        def insert_coin(value):
            """Simulate a coin insertion."""
            # Small random delay to increase chance of race condition
            time.sleep(0.001)
            store.increment_nested(
                "total_donation_cents",
                "amount",
                value,
                "timestamp"
            )

        # Create threads for each coin insertion
        threads = []
        expected_total = 0
        for i in range(num_insertions):
            coin_value = coin_values[i % len(coin_values)]
            expected_total += coin_value
            thread = threading.Thread(target=insert_coin, args=(coin_value,))
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify final total
        final_data = store.get("total_donation_cents")
        assert final_data["amount"] == expected_total, \
            f"Race condition detected: expected {expected_total}, got {final_data['amount']}"
