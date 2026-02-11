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
| **phpMyAdmin** | http://localhost:8080 | root / 123456789 |
| **MariaDB** | localhost:3306 | wallet_passes DB |

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

## Configuration

Edit `configs.py` to customize:
- Google Wallet Issuer ID
- Service account credentials path
- Database connection settings
- API server settings

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
├── main.py                 # Main Flet application
├── api/                    # FastAPI backend
│   ├── api.py             # API routes
│   └── models.py          # Data models
├── database/              # Database management
├── ui/                    # UI components
│   ├── class_builder.py   # Template Builder
│   ├── pass_generator.py  # Pass Generator
│   └── components/        # Reusable UI components
├── wallet_service.py      # Google Wallet API client
├── json_templates.py      # Pass templates
├── start_all.sh          # Linux/Mac startup script
├── start_all.bat         # Windows startup script
└── docker-compose.yml    # Docker services config
```

## License

This project is for educational and development purposes.
