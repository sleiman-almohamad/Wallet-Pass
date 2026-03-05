# Models Package

Provider-agnostic domain dataclasses. These represent business entities independent of any specific wallet provider (Google, Apple) or storage backend.

## Files

| File | Class | Description |
|------|-------|-------------|
| `passes.py` | `WalletPass` | Represents a single wallet pass. Includes `provider` field (`"google"` or `"apple"`) for future multi-provider support. |
| `notifications.py` | `NotificationAttempt` | Records a push-notification attempt with status, timestamp, and error detail. |

## Usage

```python
from models.passes import WalletPass
from models.notifications import NotificationAttempt

pass_obj = WalletPass(
    object_id="pass_001",
    class_id="event_class_001",
    holder_name="John Doe",
    holder_email="john@example.com",
    provider="google",
)

notification = NotificationAttempt(
    pass_id="pass_001",
    message="Your event has been updated!",
    provider="google",
    status="sent",
)
```
