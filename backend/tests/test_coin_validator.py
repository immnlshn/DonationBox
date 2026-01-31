"""
Test script for CoinValidator component.
Tests the coin validator without full application setup.
"""
import asyncio
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, '/home/isohn/PycharmProjects/DonationBox')

from backend.gpio.components.gpio_coin_validator import GPIOCoinValidator
from backend.gpio.event import GPIOEvent


class TestCoinHandler:
    """Simple handler to test coin events."""

    def __init__(self):
        self.coin_count = 0
        self.total_pulses = 0

    def handle_event(self, event: GPIOEvent):
        """Handle GPIO events."""
        if event.event_type == "coin_pulse":
            pulse_count = event.data["pulse_count"]
            logger.debug(f"Pulse detected! Total: {pulse_count}")

        elif event.event_type == "coin_inserted":
            self.coin_count += 1
            pulse_count = event.data["pulse_count"]
            self.total_pulses += pulse_count

            logger.info("=" * 50)
            logger.info(f"COIN INSERTED!")
            logger.info(f"Pulses: {pulse_count}")
            logger.info(f"Total coins processed: {self.coin_count}")
            logger.info(f"Total pulses: {self.total_pulses}")
            logger.info("=" * 50)


async def main():
    """Main test function."""
    logger.info("Starting CoinValidator test...")
    logger.info("Press CTRL+C to stop")

    # Create handler
    handler = TestCoinHandler()

    # Create coin validator
    validator = GPIOCoinValidator(
        component_id="test_validator",
        pin=23,
        pulse_timeout=0.3,
        bounce_time=0.01,
    )

    # Set event callback
    validator.set_event_callback(handler.handle_event)

    try:
        # Start validator
        validator.start()
        logger.info("Validator started. Waiting for coins...")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nStopping...")
    finally:
        validator.stop()
        logger.info("Test finished.")
        logger.info(f"Total coins processed: {handler.coin_count}")
        logger.info(f"Total pulses: {handler.total_pulses}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
