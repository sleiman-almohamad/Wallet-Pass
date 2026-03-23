"""
Manage Templates View
Extracted from main.py — 3-panel layout for managing Google Wallet template classes.
"""

import flet as ft
from ui.components.json_editor import JSONEditor
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
from ui.components.preview_builder import build_comprehensive_preview
from core.json_templates import get_editable_fields
import configs


def build_manage_templates_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Manage Templates tab content.

    Args:
        page:       Flet page reference
        state:      AppState (we use state.template_state for data)
        api_client: APIClient for backend calls
    """
    ts = state.template_state  # shorthand for the sub-state

    # ── Local mutable refs (UI-only, not part of global state) ──
    manage_json_editor = None
    manage_dynamic_form = None
    manage_current_json = {}
    manage_current_class_type = None
    manage_row_editor = None

    # Left panel reference for resizing
    left_panel = ft.Container(
        width=380,
        padding=15,
        bgcolor="white"
    )

    # ── UI Controls ──
    manage_templates_dropdown = ft.Dropdown(
        label=state.t("label.select_template"),
        hint_text=state.t("label.select_template"),
        width=400,
        options=[],
    )

    manage_status = ft.Text("", size=12)

    edit_class_id_field = ft.TextField(
        label=state.t("label.class_id"), width=400
    )
    edit_class_type_field = ft.TextField(
        label=state.t("label.class_type"), width=400, read_only=True, bgcolor="grey100"
    )

    manage_form_container = ft.Column(
        controls=[ft.Text(state.t("msg.load_template_hint"), color="grey", size=11)],
        spacing=8,
        scroll="auto",
    )

    notification_message_field = ft.TextField(
        label=state.t("label.notification_message"),
        hint_text=state.t("label.notification_message"),
        width=350,
        multiline=True,
        min_lines=2,
        max_lines=4,
    )

    manage_json_container = ft.Container(
        content=ft.Text(state.t("msg.load_json_hint"), color="grey", size=11),
        expand=True,
    )
    manage_preview_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text(state.t("msg.preview_hint"), size=12, color="grey"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
    )

    # ── Helpers ──

    def _set_status(msg, color="green"):
        manage_status.value = msg
        manage_status.color = color



    # ── Business-logic handlers ──

    def startup_sync_classes():
        """Check local DB; do not auto-sync from Google (local is source of truth)."""
        try:
            classes = api_client.get_classes() if api_client else []
            if not classes or len(classes) == 0:
                _set_status(
                    "ℹ️ No templates found locally. Google class sync is disabled (local DB is source of truth).",
                    "orange",
                )
                page.update()
        except Exception as e:
            _set_status(f"❌ Error checking local database: {e}", "red")
            page.update()

    def load_template_classes():
        """Load classes from local database into dropdown."""
        try:
            classes = api_client.get_classes() if api_client else []
            if classes and len(classes) > 0:
                manage_templates_dropdown.options = [
                    ft.dropdown.Option(key=cls["class_id"], text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})")
                    for cls in classes
                ]
                manage_templates_dropdown.value = classes[0]["class_id"]
                manage_templates_dropdown.hint_text = ""
                _set_status(state.t("msg.loaded_classes", count=len(classes)))
            else:
                manage_templates_dropdown.options = []
                manage_templates_dropdown.value = None
                manage_templates_dropdown.hint_text = state.t("msg.no_templates")
                _set_status(state.t("msg.no_templates"), "blue")
            page.update()
        except Exception as e:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error loading classes from database: {e}", "red")
            page.update()

    def show_template(e):
        """Fetch and display template for editing from local database."""
        nonlocal manage_json_editor, manage_current_json, manage_current_class_type, manage_dynamic_form

        if not manage_templates_dropdown.value:
            _set_status(state.t("msg.select_class_err"), "red"); page.update(); return

        _set_status(state.t("msg.loading_template"), "blue"); page.update()

        try:
            class_id = manage_templates_dropdown.value
            class_data = api_client.get_class(class_id) if api_client else None
            if not class_data:
                _set_status(state.t("msg.template_not_found", id=class_id), "red"); page.update(); return

            # Use class_json if available
            if class_data.get("class_json"):
                json_data = class_data["class_json"]
            else:
                json_data = {
                    "id": f"{configs.ISSUER_ID}.{class_id}",
                    "issuerName": class_data.get("issuer_name", state.t("placeholder.business_name")),
                    "hexBackgroundColor": class_data.get("base_color", "#4285f4"),
                }
                if class_data.get("logo_url"):
                    json_data["logo"] = {"sourceUri": {"uri": class_data["logo_url"]}}

            class_type = class_data.get("class_type", "Generic")

            # IMPORTANT: Our DB stores Generic text modules in relational form as `text_module_rows`.
            # The Manage Templates UI expects `text_module_rows` to exist in the JSON it edits,
            # but `class_json` coming from Google does not include that structure.
            if class_type == "Generic":
                # Generic class is rules-only; do NOT inject text_module_rows or branding.
                # Strip any branding fields that may have been synthesized by _build_class_json.
                for key in ["issuerName", "header", "cardTitle", "logo", "heroImage",
                            "hexBackgroundColor", "reviewStatus", "textModulesData",
                            "text_module_rows"]:
                    json_data.pop(key, None)

            edit_class_id_field.value = class_id
            edit_class_type_field.value = class_type

            manage_current_json = json_data.copy()
            manage_current_class_type = class_type

            field_mappings = get_editable_fields(class_type)

            def on_manage_form_change(updated_json):
                nonlocal manage_current_json
                manage_current_json = updated_json
                if manage_json_editor:
                    manage_json_editor.update_json(updated_json)
                # Update preview
                manage_preview_container.content = build_comprehensive_preview(updated_json, state=state)
                page.update()

            custom_form_controls = []
            nonlocal manage_row_editor

            if class_type == "Generic":
                # Generic classes are rules-only; no text module row editor.
                manage_row_editor = None
                custom_form_controls.append(ft.Container(height=5))
                custom_form_controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon("info_outline", color="blue", size=18),
                            ft.Text(
                                state.t("msg.generic_visuals_per_pass") if hasattr(state, 't') else
                                "ℹ️ Generic pass visuals/content are edited per pass in Manage Passes.",
                                size=12, color="blue700", italic=True,
                            ),
                        ], spacing=6),
                        bgcolor="blue50", padding=10, border_radius=8,
                    )
                )
            else:
                manage_row_editor = None

            manage_dynamic_form = DynamicForm(field_mappings, manage_current_json, state=state, on_change_callback=on_manage_form_change, custom_controls=custom_form_controls)
            manage_form_container.controls = manage_dynamic_form.build()

            manage_json_editor = JSONEditor(manage_current_json, state=state, read_only=True)
            manage_json_container.content = manage_json_editor.build()

            # Initial preview
            manage_preview_container.content = build_comprehensive_preview(manage_current_json, state=state)

            _set_status(state.t("msg.template_loaded"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_and_sync_handler(e):
        """Save template changes to local database AND sync to Google Wallet."""
        nonlocal manage_current_json, manage_dynamic_form, manage_row_editor

        if not edit_class_id_field.value:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return
        if not manage_dynamic_form:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return

        _set_status("⏳ Updating locally and syncing to Google...", "blue"); page.update()
        try:
            updated_json = manage_dynamic_form.get_json_data()
            extras = {}

            # Perform the update with sync_to_google=True
            response = api_client.update_class(
                class_id=edit_class_id_field.value,
                class_type=edit_class_type_field.value,
                class_json=updated_json,
                sync_to_google=True,
                **extras
            )
            _set_status("✅ " + response.get("message", state.t("msg.synced_google")))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    # ── Startup ──
    # startup_sync_classes() # Disabled per user request
    load_template_classes()

    left_panel.content = ft.Column([
                    ft.Text(state.t("header.manage_templates"), size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.manage_templates"), size=11, color="grey"),
                    ft.Divider(),
                    ft.Container(height=10),
                    manage_templates_dropdown,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        state.t("btn.show"), icon="visibility", on_click=show_template,
                        style=ft.ButtonStyle(bgcolor="green", color="white"),
                    ),
                    ft.Divider(height=20),
                    ft.Text(state.t("header.manage_templates") + " Details", size=16, weight=ft.FontWeight.BOLD),
                    edit_class_id_field,
                    edit_class_type_field,
                    ft.Container(height=5),
                    ft.Text(state.t("label.editable_fields"), size=14, weight=ft.FontWeight.W_500, color="grey700"),
                    manage_form_container,
                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        "Update & Sync to Google", icon="cloud_sync", on_click=update_and_sync_handler, width=350,
                        style=ft.ButtonStyle(bgcolor="blue", color="white"),
                    ),
                    ft.Container(height=10),
                    manage_status,
                ], spacing=8, scroll="auto")
                
    # Splitter logic
    def on_pan_update(e: ft.DragUpdateEvent):
        new_width = left_panel.width + e.delta_x
        # Constrain width between 300 and 800 pixels
        left_panel.width = max(300, min(800, new_width))
        left_panel.update()

    splitter = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        drag_interval=10,
        on_pan_update=on_pan_update,
        content=ft.Container(width=5, bgcolor="transparent")
    )

    # ── 3-panel layout ──
    return ft.Container(
        content=ft.Row([
            # Left Panel: Controls and Edit Fields
            left_panel,
            splitter,
            
            # Middle Panel: JSON Configuration
            ft.Container(
                width=320,
                content=ft.Column([
                    ft.Text(state.t("label.json_config"), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.complete_json"), size=10, color="grey"),
                    ft.Container(height=10),
                    manage_json_container,
                ], scroll="auto"),
                padding=15, bgcolor="grey50",
            ),
            # Right Panel: Live Preview
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text(state.t("label.visual_preview"), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.pass_look"), size=10, color="grey"),
                    ft.Container(height=20),
                    manage_preview_container,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, bgcolor="grey100",
            ),
        ], expand=True, spacing=0),
        expand=True,
    )
