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
