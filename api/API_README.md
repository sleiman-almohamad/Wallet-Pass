# Wallet Passes API

A RESTful API built with FastAPI for managing Google Wallet pass classes and passes.

## Features

- ✅ Full CRUD operations for pass classes
- ✅ Full CRUD operations for passes
- ✅ Email-based pass lookup
- ✅ Class-based pass filtering
- ✅ Status-based filtering (Active/Expired)
- ✅ Interactive API documentation (Swagger UI)
- ✅ CORS support for web applications
- ✅ Pydantic validation for all requests

## Installation

Dependencies are already configured in `pyproject.toml`. To install:

```bash
uv sync
```

## Running the API

### Option 1: Using the startup script
```bash
./start_api.sh
```

### Option 2: Using uvicorn directly
```bash
uv run uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

### Automated Test Script

Run the test suite from the project root:
```bash
# Make sure the API is running first
uv run python api/test_api.py
```

### Option 3: Using Python
```bash
uv run python -m api.api
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /health` - Check API and database health status

### Classes Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/classes/` | Create a new pass class |
| GET | `/classes/` | Get all pass classes |
| GET | `/classes/{class_id}` | Get a specific class |
| PUT | `/classes/{class_id}` | Update a class |
| DELETE | `/classes/{class_id}` | Delete a class |

### Passes Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/passes/` | Create a new pass |
| GET | `/passes/` | Get all passes (optional status filter) |
| GET | `/passes/{object_id}` | Get a specific pass |
| GET | `/passes/class/{class_id}` | Get all passes for a class |
| GET | `/passes/email/{email}` | Get all passes for an email |
| PUT | `/passes/{object_id}` | Update a pass |
| PUT | `/passes/{object_id}/status` | Update pass status only |
| DELETE | `/passes/{object_id}` | Delete a pass |

## Usage Examples

### Create a Class

```bash
curl -X POST "http://localhost:8000/classes/" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "EVENT_CLASS_001",
    "class_type": "EventTicket",
    "base_color": "#FF5733",
    "logo_url": "https://example.com/logo.png"
  }'
```

### Get All Classes

```bash
curl "http://localhost:8000/classes/"
```

### Create a Pass

```bash
curl -X POST "http://localhost:8000/passes/" \
  -H "Content-Type: application/json" \
  -d '{
    "object_id": "PASS_001",
    "class_id": "EVENT_CLASS_001",
    "holder_name": "John Doe",
    "holder_email": "john.doe@example.com",
    "status": "Active",
    "pass_data": {
      "seat": "A12",
      "gate": "Gate 5",
      "match_time": "2024-12-15T19:00:00"
    }
  }'
```

### Get All Active Passes

```bash
curl "http://localhost:8000/passes/?status=Active"
```

### Get Passes by Email

```bash
curl "http://localhost:8000/passes/email/john.doe@example.com"
```

### Update Pass Status

```bash
curl -X PUT "http://localhost:8000/passes/PASS_001/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Expired"
  }'
```

### Delete a Pass

```bash
curl -X DELETE "http://localhost:8000/passes/PASS_001"
```

## Interactive Documentation

The easiest way to test the API is through the interactive Swagger UI:

1. Start the API server
2. Open http://localhost:8000/docs in your browser
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint
5. Fill in the parameters and click "Execute"

## Data Models

### ClassCreate
```json
{
  "class_id": "string",
  "class_type": "string",
  "base_color": "string (optional)",
  "logo_url": "string (optional)"
}
```

### PassCreate
```json
{
  "object_id": "string",
  "class_id": "string",
  "holder_name": "string",
  "holder_email": "email",
  "status": "Active|Expired",
  "pass_data": {
    "key": "value"
  }
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict (duplicate entry)
- `500` - Internal Server Error

Error responses include a detail message:
```json
{
  "detail": "Error description"
}
```

## Database Configuration

The API uses the database configuration from `configs.py`:
- Host: 127.0.0.1
- Port: 3306
- Database: wallet_passes

Make sure your MariaDB database is running before starting the API.

## CORS Configuration

CORS is enabled for all origins by default. For production, update the `allow_origins` in `api.py` to specify allowed domains.

## Development

The API runs in reload mode by default, so any changes to the code will automatically restart the server.

## Notes

- All endpoints validate input using Pydantic models
- Email addresses are validated using the `email-validator` library
- JSON data in passes is automatically serialized/deserialized
- Deleting a class will cascade delete all associated passes
- The database manager handles connection pooling and error handling
