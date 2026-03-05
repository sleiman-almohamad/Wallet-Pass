# State Package

Application state management using the **observer pattern**. Each sub-state holds data for a specific concern and notifies subscribers when values change.

## Architecture

```
AppState                    ← created once in main()
├── template_state          ← ManageTemplateState (Manage Templates tab)
├── pass_state              ← ManagePassState (Manage Passes tab)
└── apple_state             ← AppleState (placeholder for future Apple Wallet)
```

## Files

| File | Class(es) | Description |
|------|-----------|-------------|
| `app_state.py` | `AppState` | Root coordinator. Holds service references (`api_client`, `wallet_client`) and sub-state instances. |
| `google_state.py` | `ManageTemplateState`, `ManagePassState` | Observer-pattern sub-states for the two Google Wallet management tabs. |
| `apple_state.py` | `AppleState` | Placeholder with no-op methods for future Apple Wallet / PassKit support. |

## Observer Pattern

```python
from state.app_state import AppState

state = AppState(page, api_client, wallet_client)

# Subscribe to template state changes
def on_template_change(data: dict):
    print("Template state changed:", data)

state.template_state.subscribe(on_template_change)

# Update state (triggers all subscribers)
state.template_state.update("selected_class_id", "my_class")
state.template_state.set_status("✅ Loaded!", "green")
```
