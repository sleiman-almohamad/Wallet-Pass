"""
Domain model for wallet passes — provider-agnostic.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WalletPass:
    """Represents a single wallet pass, independent of provider."""

    object_id: str
    class_id: str
    holder_name: str
    holder_email: str
    status: str = "Active"
    provider: str = "google"          # "google" | "apple"
    pass_data: dict = field(default_factory=dict)
    class_type: Optional[str] = None  # e.g. "EventTicket", "Generic"

    @property
    def is_google(self) -> bool:
        return self.provider == "google"

    @property
    def is_apple(self) -> bool:
        return self.provider == "apple"
