"""
Bot Executor — delegates all broker calls to the Pepperstone service.
This thin shim means the bot engine never imports broker-specific code directly.
If you ever switch brokers again, only this file + pepperstone.py need changing.
"""
from services.pepperstone import (
    get_open_trade,
    place_order,
    close_trade,
    get_account_balance,
)

__all__ = [
    "get_open_trade",
    "place_order",
    "close_trade",
    "get_account_balance",
]
