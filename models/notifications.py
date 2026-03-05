"""
Domain model for notification attempts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NotificationAttempt:
    """Records a single push-notification attempt."""

    pass_id: str
    message: str
    provider: str = "google"          # "google" | "apple"
    status: str = "pending"           # "pending" | "sent" | "failed"
    timestamp: Optional[datetime] = None
    error_detail: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
