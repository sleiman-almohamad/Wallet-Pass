import os
from dotenv import load_dotenv

load_dotenv()

# Issuer ID
ISSUER_ID = os.getenv("ISSUER_ID")

# Default key file name
KEY_FILE_PATH = os.getenv("KEY_FILE_PATH")

# Default scopes
SCOPES = [s.strip() for s in os.getenv(
    "SCOPES",
    "https://www.googleapis.com/auth/wallet_object.issuer"
).split(",")]

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "wallet_passes")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8100"))

# ---------------------------------------------------------------------------
# Sync controls
# ---------------------------------------------------------------------------
# Permanent safety: treat local DB as the source of truth for Classes.
# Google Wallet GenericClass responses omit many branding fields, so syncing
# classes FROM Google can wipe local data. Keep this disabled by default.
ALLOW_GOOGLE_CLASS_SYNC = os.getenv("ALLOW_GOOGLE_CLASS_SYNC", "false").lower() in ("1", "true", "yes", "y", "on")

# Pass sync can still be allowed independently.
ALLOW_GOOGLE_PASS_SYNC = os.getenv("ALLOW_GOOGLE_PASS_SYNC", "true").lower() in ("1", "true", "yes", "y", "on")

# ---------------------------------------------------------------------------
# Apple Wallet
# ---------------------------------------------------------------------------
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_PASS_TYPE_ID = os.getenv("APPLE_PASS_TYPE_ID")
APPLE_CERT_PATH = os.getenv("APPLE_CERT_PATH", "certs/pass_certificate.pem")
APPLE_KEY_PATH = os.getenv("APPLE_KEY_PATH", "certs/pass_key.pem")
APPLE_WWDR_PATH = os.getenv("APPLE_WWDR_PATH", "certs/wwdr.pem")
APPLE_KEY_PASSWORD = os.getenv("APPLE_KEY_PASSWORD", "")
# My ngrok/cloudflare url (Backend)
APPLE_WEB_SERVICE_URL = os.getenv("APPLE_WEB_SERVICE_URL", "https://breeding-caddy-fondly.ngrok-free.dev")
# Public URL for Google Wallet images and callbacks
PUBLIC_URL = os.getenv("PUBLIC_URL", APPLE_WEB_SERVICE_URL)
