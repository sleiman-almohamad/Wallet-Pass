# Core Package

Domain logic, schemas, templates, and parsers shared across the application.

## Files

| File | Description |
|------|-------------|
| `field_schemas.py` | Field definitions for each pass class type (EventTicket, LoyaltyCard, Generic, etc.). Used by the UI to render dynamic forms. |
| `json_templates.py` | `JSONTemplateManager` class and helpers (`get_template`, `get_editable_fields`) for building and querying Google Wallet JSON structures. |
| `google_wallet_parser.py` | `parse_google_wallet_class()` — extracts relational metadata (issuer name, colors, logo URL, etc.) from raw Google Wallet class JSON. Used during sync and API updates. |
| `qr_generator.py` | `generate_qr_code()` — creates QR code images (as base64 data URIs) for "Add to Google Wallet" links. |

## Usage

```python
from core.json_templates import get_template, get_editable_fields
from core.field_schemas import get_fields_for_class_type
from core.google_wallet_parser import parse_google_wallet_class
from core.qr_generator import generate_qr_code
```
