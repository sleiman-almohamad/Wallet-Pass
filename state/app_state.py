"""
Application State — Root coordinator
Holds references to services and sub-states for every wallet provider.
"""

from .google_state import ManageTemplateState, ManagePassState, ManageNotificationState
from .apple_state import AppleState
from i18n.translations import TRANSLATIONS


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
        self.notification_state = ManageNotificationState()

        # Apple Wallet sub-state (placeholder)
        self.apple_state = AppleState()

        # Localization
        self.language = "en"

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

    def set_language(self, lang: str):
        """Update current language and refresh UI."""
        if lang in TRANSLATIONS:
            self.language = lang
            if self.page:
                self.page.update()

    def t(self, key: str, **kwargs) -> str:
        """Translate a key into the current language."""
        # Fallback order: current lang -> en -> key
        text = TRANSLATIONS.get(self.language, {}).get(key)
        if text is None:
            text = TRANSLATIONS.get("en", {}).get(key, key)
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
