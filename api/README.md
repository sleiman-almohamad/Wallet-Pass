# API Package

FastAPI backend providing REST endpoints for the Flet desktop app to manage pass classes, pass objects, notifications, and Google Wallet sync.

## Files

| File | Description |
|------|-------------|
| `api.py` | All FastAPI route handlers — classes CRUD, passes CRUD, sync from Google Wallet, health check, notifications log. |
| `models.py` | Pydantic request/response models for API validation. |

## Running

```bash
uv run python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (API + database) |
| `GET` | `/classes` | List all classes |
| `POST` | `/classes` | Create a class |
| `PUT` | `/classes/{class_id}` | Update a class (optionally sync to Google) |
| `GET` | `/passes` | List all passes |
| `GET` | `/passes/{object_id}` | Get a single pass |
| `PUT` | `/passes/{object_id}` | Update a pass |
| `POST` | `/sync/classes` | Sync classes from Google Wallet |
| `POST` | `/sync/passes` | Sync passes from Google Wallet |

## API Docs

Interactive Swagger UI: **http://localhost:8000/docs**
