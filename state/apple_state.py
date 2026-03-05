"""
Apple Wallet State Management — Placeholder
Future home for Apple Wallet / PassKit sub-state.
"""


class AppleState:
    """Placeholder sub-state for future Apple Wallet support.

    Mirrors the interface shape of the Google sub-states so that
    `AppState` can treat providers uniformly.
    """

    def load_classes(self):
        """Load Apple pass type identifiers — not yet implemented."""
        pass

    def load_passes(self):
        """Load passes from Apple — not yet implemented."""
        pass

    def sync(self):
        """Sync with Apple servers — not yet implemented."""
        pass

    def send_notification(self, pass_id: str, message: str):
        """Push an update notification — not yet implemented."""
        pass
