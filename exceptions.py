"""
Custom exceptions for the WalletPasses application.

Hierarchy
─────────
WalletPassError
├── DatabaseError
│   ├── RecordNotFoundError
│   └── DuplicateRecordError
├── GoogleWalletError
│   ├── GoogleWalletAPIError
│   ├── GoogleWalletNotFoundError
│   └── GoogleWalletSyncError
├── ValidationError
└── APIClientError
    └── APIClientHTTPError
"""


class WalletPassError(Exception):
    """Base exception for all WalletPasses errors."""


# ── Database layer ───────────────────────────────────────────────────────

class DatabaseError(WalletPassError):
    """Any error originating from the database layer."""


class RecordNotFoundError(DatabaseError):
    """Raised when a requested database record does not exist."""


class DuplicateRecordError(DatabaseError):
    """Raised when an insert would violate a unique constraint."""


# ── Google Wallet API layer ──────────────────────────────────────────────

class GoogleWalletError(WalletPassError):
    """Base for all Google Wallet API-related errors."""


class GoogleWalletAPIError(GoogleWalletError):
    """HTTP-level failure returned by the Google Wallet API."""

    def __init__(self, message: str, *, status_code: int | None = None,
                 detail: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class GoogleWalletNotFoundError(GoogleWalletError):
    """Raised when a class or object is not found in Google Wallet (404)."""


class GoogleWalletSyncError(GoogleWalletError):
    """Raised when synchronisation between local DB and Google Wallet fails."""


# ── Validation ───────────────────────────────────────────────────────────

class ValidationError(WalletPassError):
    """Raised when input data fails validation."""


# ── Internal API client (Streamlit → FastAPI) ────────────────────────────

class APIClientError(WalletPassError):
    """Base for errors raised by the internal API client."""


class APIClientHTTPError(APIClientError):
    """HTTP-level failure when calling the FastAPI backend."""

    def __init__(self, message: str, *, status_code: int | None = None,
                 detail: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)
