"""
GPIO Components package.

Components can be auto-registered by importing them here.
Use setup_components() to register all defined components with the registry.
"""

__all__ = ["setup_components"]

from backend.gpio.components.chose_category_button import ChooseCategoryButton
from backend.gpio.components.gpio_coin_validator import GPIOCoinValidator
from backend.gpio.components.donation_coin_validator import DonationCoinValidator


def setup_components(registry):
  """
  Setup and register all GPIO components.

  Define your components here directly - no config file needed.
  Dependencies are injected into handlers at runtime.

  Args:
      registry: ComponentRegistry instance
  """
  vote_button_1 = ChooseCategoryButton("category_button_1", 1, pin=22, bounce_time=0.1)
  vote_button_2 = ChooseCategoryButton("category_button_2", 2, pin=27, bounce_time=0.1)
  registry.register(vote_button_1)
  registry.register(vote_button_2)

  coin_validator = DonationCoinValidator(
      component_id="coin_validator",
      pin=23,
      pulse_timeout=0.3,
      bounce_time=0.01,
      debounce_seconds=10.0
  )
  registry.register(coin_validator)



