"""
Application State — Root coordinator
Holds references to services and sub-states for every wallet provider.
"""

from .google_state import ManageTemplateState, ManagePassState
from .apple_state import AppleState


class AppState:
    """Central application state, created once in ``main()``."""

    def __init__(self, page, api_client, wallet_client=None):
        # Flet page reference (for page-level operations)
        self.page = page

        # Service references
        self.api_client = api_client
        self.wallet_client = wallet_client

        # Connection status
        self.wallet_connected: bool = wallet_client is not None
        self.api_connected: bool = False

        # Google Wallet sub-states
        self.template_state = ManageTemplateState()
        self.pass_state = ManagePassState()

        # Apple Wallet sub-state (placeholder)
        self.apple_state = AppleState()

    # -- Convenience helpers ------------------------------------------------

    def check_api_health(self) -> dict:
        """Ping the backend API and store connection status."""
        try:
            health = self.api_client.check_health()
            self.api_connected = health.get("status") == "healthy"
            return health
        except Exception as exc:
            self.api_connected = False
            return {"status": "error", "detail": str(exc)}

    def send_notification(self, pass_id: str, message: str, provider: str = "google"):
        """Route a notification to the correct provider service."""
        if provider == "google":
            # Delegated to google_wallet_service via the caller
            raise NotImplementedError("Use template_state / pass_state methods directly for now")
        elif provider == "apple":
            self.apple_state.send_notification(pass_id, message)
        else:
            raise ValueError(f"Unknown provider: {provider}")
