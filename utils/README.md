# Utils Package

Shared helper functions used across multiple packages.

## Files

| File | Functions | Description |
|------|-----------|-------------|
| `formatting.py` | `status_text()`, `set_status()` | Create and update Flet status-text controls with color-coded messages. |
| `validation.py` | `ensure_issuer_prefix()`, `strip_issuer_prefix()` | Add or remove the Google Wallet issuer ID prefix from class/object IDs. |

## Usage

```python
from utils.formatting import status_text, set_status
from utils.validation import ensure_issuer_prefix, strip_issuer_prefix

# Create a status label
label = status_text("Ready", color="green")

# Ensure proper ID format
full_id = ensure_issuer_prefix("my_class")   # → "3388000000023033675.my_class"
short_id = strip_issuer_prefix(full_id)      # → "my_class"
```
