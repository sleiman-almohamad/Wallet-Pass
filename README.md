# Google Wallet Verifier & Preview

A desktop application for creating, managing, and generating Google Wallet passes with visual preview and QR code generation.

## Features

- **Template Builder**: Create pass class templates with dynamic forms
- **Manage Templates**: Edit existing templates with field-based editing
- **Pass Generator**: Generate individual passes with QR codes
- **Pass Verifier**: Verify existing Google Wallet passes
- **Visual Preview**: Real-time pass visualization
- **Database Management**: Local MariaDB storage with phpMyAdmin

## Prerequisites

### Required Software

- **Python 3.10+**
- **uv** package manager - Install: `pip install uv`
- **Docker Desktop** (for database services)
- **Google Cloud Service Account Key**: Place your `*.json` key file in the project root

### Operating Systems

- ✅ Linux
- ✅ Windows (with Docker Desktop)
- ✅ macOS (with Docker Desktop)

## Quick Start

### For Linux/macOS Users

```bash
# Make the script executable (first time only)
chmod +x start_all.sh

# Run the application
./start_all.sh
```

### For Windows Users

```batch
REM Double-click start_all.bat or run from CMD
start_all.bat
```

### What the Startup Scripts Do

1. **Start Docker services** (MariaDB + phpMyAdmin)
2. **Start FastAPI backend** (http://localhost:8000)
3. **Launch Flet GUI** application

## Manual Setup

If you prefer manual control:

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start Docker Services

```bash
# Linux/macOS
sudo docker compose up -d

# Windows
docker compose up -d
```

### 3. Start FastAPI Server

```bash
uv run python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run the Application

```bash
uv run python main.py
```

## Available Services

Once started, the following services are available:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Flet App** | Desktop GUI | N/A |
| **FastAPI** | http://localhost:8000 | N/A |
| **API Docs** | http://localhost:8000/docs | N/A |
| **phpMyAdmin** | http://localhost:8080 | See `.env` |
| **MariaDB** | localhost:3306 | See `.env` |

## Configuration

All sensitive configuration (credentials, API keys, database passwords) is loaded from environment variables via a `.env` file. **The `.env` file is gitignored and never committed.**

### First-Time Setup

1. **Copy the example file** to create your own `.env`:

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and fill in your real credentials:

   ```dotenv
   # Google Wallet
   ISSUER_ID=your_issuer_id_here
   KEY_FILE_PATH=your-service-account-key.json

   # Database
   DB_USER=root
   DB_PASSWORD=your_db_password
   ```

3. **Place your Google Cloud service account key** (`.json` file) in the project root.

### How It Works

- `configs.py` reads all values from environment variables using `python-dotenv`.
- Non-sensitive values like `DB_HOST`, `DB_PORT`, and `DB_NAME` have sensible defaults.
- Sensitive values like `ISSUER_ID`, `KEY_FILE_PATH`, `DB_USER`, and `DB_PASSWORD` **must** be set in `.env` — they have no defaults.
- `.env.example` is a template with placeholder values that is safe to commit and share.

## Database Sync

### Import Classes from Google Wallet

If you have existing classes in Google Wallet and want to load them into your local database:

```bash
# Make sure the API server is running first
uv run python -m uvicorn api.api:app --reload

# In another terminal, run the sync script
uv run python database/sync_from_google.py
```

This will:
- Fetch **all** classes from your Google Wallet account
- Import them into the local database
- Preserve the complete JSON structure
- Update existing classes if already in database

Perfect for:
- Setting up a new development environment
- Syncing production classes to local testing
- Sharing templates with your supervisor/team

### Syncing from Google Wallet

The application automatically syncs templates from Google Wallet on startup if the local database is empty.

If you need to re-sync, restart the application.

## Usage

### 1. Template Builder
Create new pass class templates:
- Choose pass type (Generic, LoyaltyCard, EventTicket, etc.)
- Fill in template fields dynamically
- Set colors, logos, and hero images
- Save to local database
- Optionally insert to Google Wallet

### 2. Manage Templates
Edit existing templates:
- Load templates from local database
- Edit fields with dynamic forms
- Update in local database
- Sync changes to Google Wallet API

### 3. Pass Generator
Generate individual passes:
- Select template from dropdown
- Fill in holder information
- Enter pass-specific data (seat, points, etc.)
- Generate pass with QR code
- Scan QR to add to Google Wallet

### 4. Pass Verifier
Verify existing passes:
- Enter pass Object ID
- View pass and class details
- Visual preview of the pass

## Troubleshooting

### Windows-Specific Issues

**Docker not starting:**
- Ensure Docker Desktop is installed and running
- Check Docker settings allow resource sharing

**Script permission errors:**
- Right-click `start_all.bat` → "Run as administrator"

### General Issues

**Database connection errors:**
- Ensure Docker services are running: `docker ps`
- Restart Docker services: `docker compose restart`

**API connection refused:**
- Check if FastAPI server is running
- Verify port 8000 is not in use

**Module not found:**
- Run `uv sync` to install dependencies
- Ensure you're in the project directory

## Development

### Project Structure

```
WalletPasses/
├── main.py                         # Entry point (41 lines — bootstrap only)
├── configs.py                      # Global configuration (issuer ID, DB creds, etc.)
│
├── core/                           # Domain logic, schemas, templates
│   ├── field_schemas.py            # Field definitions per pass type
│   ├── json_templates.py           # JSON template manager
│   ├── google_wallet_parser.py     # Parse Google Wallet class JSON
│   └── qr_generator.py            # QR code generation
│
├── state/                          # Application state (observer pattern)
│   ├── app_state.py                # Root AppState coordinator
│   ├── google_state.py             # ManageTemplateState + ManagePassState
│   └── apple_state.py              # Future Apple Wallet placeholder
│
├── views/                          # Flet UI screens
│   ├── root_view.py                # Header + tabs assembly
│   ├── manage_templates_view.py    # Manage Templates tab (3-panel layout)
│   └── manage_passes_view.py       # Manage Passes tab (3-panel layout)
│
├── services/                       # External integrations
│   ├── google_wallet_service.py    # Google Wallet API client (WalletClient)
│   ├── api_client.py               # Local FastAPI backend client (APIClient)
│   ├── class_update_service.py     # Propagate class updates to passes
│   └── apple_wallet_service.py     # Future Apple Wallet placeholder
│
├── models/                         # Provider-agnostic domain dataclasses
│   ├── passes.py                   # WalletPass
│   └── notifications.py           # NotificationAttempt
│
├── utils/                          # Shared helpers
│   ├── formatting.py               # Status message helpers
│   └── validation.py               # Issuer ID validation
│
├── ui/                             # Self-contained tab modules
│   ├── class_builder.py            # Template Builder tab
│   ├── pass_generator.py           # Pass Generator tab
│   └── components/                 # Reusable UI components
│
├── api/                            # FastAPI backend
│   ├── api.py                      # REST endpoints
│   └── models.py                   # Pydantic models
│
├── database/                       # Database layer
│   ├── db_manager.py               # DatabaseManager (CRUD)
│   ├── models.py                   # SQLAlchemy models
│   └── schema.sql/                 # SQL schema
│
├── docker-compose.yml              # MariaDB + phpMyAdmin
├── start_all.sh                    # Linux/Mac startup script
└── start_all.bat                   # Windows startup script
```

## License

This project is for educational and development purposes.
