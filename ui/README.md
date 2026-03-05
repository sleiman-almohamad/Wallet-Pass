# UI Package

Self-contained Flet UI modules for the Template Builder and Pass Generator tabs, plus reusable components.

## Files

| File | Function | Description |
|------|----------|-------------|
| `class_builder.py` | `create_template_builder(page, api_client)` | Template Builder tab — dynamic form for creating new pass class templates with live JSON and visual preview. |
| `pass_generator.py` | `create_pass_generator(page, api_client, wallet_client)` | Pass Generator tab — select a template, fill in holder info, generate a pass with QR code for Google Wallet. |

## Subdirectories

### `components/`

Reusable UI components shared across tabs:

| File | Class | Description |
|------|-------|-------------|
| `json_editor.py` | `JSONEditor` | Read-only or editable JSON display panel. |
| `json_form_mapper.py` | `DynamicForm` | Generates Flet form controls from a field-mapping schema and keeps JSON in sync. |
| `live_preview.py` | `LivePreview` | Real-time visual pass card preview. |
| `color_picker.py` | `ColorPicker` | Hex color input with preview swatch. |
| `image_uploader.py` | `ImageUploader` | URL input for logo/hero images with preview. |

### `models/`

> **Deprecated** — The old `template_state.py` lives here. New state classes are in the top-level `state/` package.
