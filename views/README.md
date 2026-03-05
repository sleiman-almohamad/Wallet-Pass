# Views Package

Flet UI screens. Each module exposes a `build_*_view(page, state, ...)` function that returns a Flet control tree.

## Files

| File | Function | Description |
|------|----------|-------------|
| `root_view.py` | `build_root_view(page, state)` | Assembles the header, connection status bar, and `ft.Tabs` container wiring all 4 tabs together. |
| `manage_templates_view.py` | `build_manage_templates_view(page, state, api_client)` | 3-panel layout (form / JSON / preview) for loading, editing, and syncing template classes. |
| `manage_passes_view.py` | `build_manage_passes_view(page, state, api_client)` | 3-panel layout for loading, editing, and pushing individual pass objects. |

## Tab Wiring

```
root_view.py
├── Tab 1: Template Builder    → ui/class_builder.py (existing module)
├── Tab 2: Pass Generator      → ui/pass_generator.py (existing module)
├── Tab 3: Manage Templates    → views/manage_templates_view.py
└── Tab 4: Manage Passes       → views/manage_passes_view.py
```

> **Note:** Template Builder and Pass Generator live in `ui/` because they predate this refactoring and are already self-contained modules.
