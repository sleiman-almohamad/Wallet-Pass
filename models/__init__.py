"""
Domain Models Package
Provider-agnostic data classes for passes, notifications, etc.
"""

from .passes import WalletPass
from .notifications import NotificationAttempt

__all__ = ["WalletPass", "NotificationAttempt"]
