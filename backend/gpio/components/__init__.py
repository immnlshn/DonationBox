"""
GPIO Components package.

Components can be auto-registered by importing them here.
Use setup_components() to register all defined components with the registry.
"""

__all__ = ["setup_components"]

from backend.gpio.components.VoteButton import VoteButton


def setup_components(registry):
  """
  Setup and register all GPIO components.

  Define your components here directly - no config file needed.

  Args:
      registry: ComponentRegistry instance
  """
  vote_button_1 = VoteButton("button_1", 1, pin=22, bounce_time=0.1)
  vote_button_2 = VoteButton("button_2", 2, pin=27, bounce_time=0.1)
  registry.register(vote_button_1)
  registry.register(vote_button_2)
