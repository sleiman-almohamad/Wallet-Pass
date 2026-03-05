# Services Package

External integrations and domain services.

## Files

| File | Class / Function | Description |
|------|-----------------|-------------|
| `google_wallet_service.py` | `WalletClient` | Full Google Wallet API client — create/read/update classes and pass objects, send notifications, list and sync passes. |
| `api_client.py` | `APIClient` | HTTP client for the local FastAPI backend (`localhost:8000`). Wraps all REST endpoints (classes, passes, sync, health check). |
| `class_update_service.py` | `propagate_class_update_to_passes()` | Domain service that propagates class template changes to all associated pass objects in Google Wallet, with push notifications. |
| `apple_wallet_service.py` | `AppleWalletService` | **Placeholder** for future Apple Wallet / PassKit integration. Stub methods raise `NotImplementedError`. |

## Usage

```python
from services.google_wallet_service import WalletClient
from services.api_client import APIClient
from services.class_update_service import propagate_class_update_to_passes

wallet_client = WalletClient()
api_client = APIClient()
```

## Adding Apple Wallet Support

When ready to implement Apple Wallet:
1. Implement the methods in `apple_wallet_service.py`
2. Wire them into `state/apple_state.py`
3. Create a new view in `views/` for Apple pass management
4. Add a new tab in `views/root_view.py`
