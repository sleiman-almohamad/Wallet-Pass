"""
Manage Templates View
Extracted from main.py — 3-panel layout for managing Google Wallet template classes.
"""

import flet as ft
from ui.components.json_editor import JSONEditor
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
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
        label="Select Template Class",
        hint_text="Choose a class to manage",
        width=400,
        options=[],
    )

    manage_status = ft.Text("", size=12)

    edit_class_id_field = ft.TextField(
        label="Class ID", width=400, read_only=True, bgcolor="grey100"
    )
    edit_class_type_field = ft.TextField(
        label="Class Type", width=400, read_only=True, bgcolor="grey100"
    )

    manage_form_container = ft.Column(
        controls=[ft.Text("Load a template to see editable fields", color="grey", size=11)],
        spacing=8,
        scroll="auto",
    )

    notification_message_field = ft.TextField(
        label="Notification Message (optional)",
        hint_text="Enter message to send to pass holders...",
        width=350,
        multiline=True,
        min_lines=2,
        max_lines=4,
    )

    manage_json_container = ft.Container(
        content=ft.Text("Load a template to see JSON", color="grey", size=11),
        expand=True,
    )
    manage_preview_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text("Preview will appear here", size=12, color="grey"),
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

    def build_manage_preview(class_data: dict) -> ft.Container:
        """Build visual pass preview for manage templates."""
        bg_color = class_data.get("hexBackgroundColor") or class_data.get("base_color", "#4285f4")

        # Logo
        logo_url = None
        if "programLogo" in class_data:
            logo_url = class_data.get("programLogo", {}).get("sourceUri", {}).get("uri")
        elif "logo" in class_data:
            logo_url = class_data.get("logo", {}).get("sourceUri", {}).get("uri")
        elif "logo_url" in class_data:
            logo_url = class_data.get("logo_url")

        # Hero
        hero_url = None
        if "heroImage" in class_data:
            hero_url = class_data.get("heroImage", {}).get("sourceUri", {}).get("uri")

        # Header / title
        header_text = "Business Name"
        card_title = "Pass Title"

        if "localizedIssuerName" in class_data:
            header_text = class_data.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
        elif "issuerName" in class_data:
            header_text = class_data.get("issuerName", "Business")
        elif "issuer_name" in class_data:
            header_text = class_data.get("issuer_name", "Business")

        if "localizedProgramName" in class_data:
            card_title = class_data.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
        elif "eventName" in class_data:
            card_title = class_data.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
        elif "header" in class_data:
            header_text = class_data.get("header", {}).get("defaultValue", {}).get("value", "Header")
        if "cardTitle" in class_data:
            card_title = class_data.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")
        elif "card_title" in class_data:
            card_title = class_data.get("card_title", "Title")

        # Build logo control
        if logo_url:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(src=logo_url, width=50, height=50, fit=ft.ImageFit.COVER),
            )
        else:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25, bgcolor="white30",
                content=ft.Icon("business", color="white", size=30),
                alignment=ft.alignment.center,
            )

        # Build hero control
        if hero_url:
            hero_control = ft.Container(
                height=150,
                content=ft.Image(src=hero_url, width=300, height=150, fit=ft.ImageFit.COVER),
            )
        else:
            hero_control = ft.Container(
                height=150, bgcolor="black12",
                content=ft.Column(
                    [ft.Icon("image", size=40, color="grey"), ft.Text("Hero Image", size=12, color="grey")],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        return ft.Container(
            width=300,
            bgcolor=bg_color,
            border_radius=15,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=15, color="black26", offset=ft.Offset(0, 5)),
            content=ft.Column([
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        logo_control,
                        ft.Container(width=10),
                        ft.Text(header_text, color="white", weight=ft.FontWeight.BOLD, size=14, expand=True),
                    ]),
                ),
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(card_title, color="white", size=20, weight=ft.FontWeight.BOLD),
                ),
                hero_control,
                ft.Container(
                    bgcolor="white", padding=15,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=11),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Container(
                                width=70, height=70, bgcolor="grey200", border_radius=5,
                                content=ft.Icon("qr_code_2", size=50, color="grey"),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text("Sample User", weight=ft.FontWeight.BOLD, size=13, color="black"),
                                ft.Text("ID: 1234567890", size=11, color="grey"),
                            ]),
                        ]),
                    ]),
                ),
            ], spacing=0),
        )

    # ── Business-logic handlers ──

    def startup_sync_classes():
        """Check local DB and sync from Google Wallet if empty."""
        try:
            classes = api_client.get_classes() if api_client else []
            if not classes or len(classes) == 0:
                _set_status("⏳ Syncing classes from Google Wallet...", "blue")
                page.update()
                try:
                    api_client.sync_classes()
                    classes = api_client.get_classes() if api_client else []
                    if classes and len(classes) > 0:
                        _set_status(f"✅ Synced {len(classes)} classes from Google Wallet")
                    else:
                        _set_status("ℹ️ No classes found in Google Wallet", "blue")
                except Exception as sync_error:
                    _set_status(f"❌ Error syncing classes: {sync_error}", "red")
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
                _set_status(f"✅ Loaded {len(classes)} template(s) from local database")
            else:
                manage_templates_dropdown.options = []
                manage_templates_dropdown.value = None
                manage_templates_dropdown.hint_text = "No templates available"
                _set_status("ℹ️ No templates found. Create one in 'Template Builder' tab or restart app to sync from Google Wallet.", "blue")
            page.update()
        except Exception as e:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error loading classes from database: {e}", "red")
            page.update()

    def show_template(e):
        """Fetch and display template for editing from local database."""
        nonlocal manage_json_editor, manage_current_json, manage_current_class_type, manage_dynamic_form

        if not manage_templates_dropdown.value:
            _set_status("❌ Please select a class", "red"); page.update(); return

        _set_status("⏳ Loading template from database...", "blue"); page.update()

        try:
            class_id = manage_templates_dropdown.value
            class_data = api_client.get_class(class_id) if api_client else None
            if not class_data:
                _set_status(f"❌ Template '{class_id}' not found in database", "red"); page.update(); return

            # Use class_json if available
            if class_data.get("class_json"):
                json_data = class_data["class_json"]
            else:
                json_data = {
                    "id": f"{configs.ISSUER_ID}.{class_id}",
                    "issuerName": class_data.get("issuer_name", "Your Business"),
                    "hexBackgroundColor": class_data.get("base_color", "#4285f4"),
                }
                if class_data.get("logo_url"):
                    json_data["logo"] = {"sourceUri": {"uri": class_data["logo_url"]}}

            class_type = class_data.get("class_type", "Generic")

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
                manage_preview_container.content = build_manage_preview(updated_json)
                page.update()

            custom_form_controls = []
            nonlocal manage_row_editor
            
            if class_type == "Generic":
                def on_rows_change(rows):
                    nonlocal manage_current_json
                    manage_current_json["text_module_rows"] = rows
                    on_manage_form_change(manage_current_json)
                
                initial_rows = manage_current_json.get("text_module_rows", [])
                if not initial_rows and "textModulesData" in manage_current_json:
                    # Normally Manage templates reads local DB so it should have text_module_rows.
                    # But if rehydrating from raw google JSON, we pass the flat structure.
                    # We will rely on TextModuleRowEditor's "pass" mode parsing logic indirectly if needed, 
                    # but here we are in "class" mode. The API handles fetching as row dicts.
                    pass
                manage_row_editor = TextModuleRowEditor(initial_rows, on_change=on_rows_change, mode="class")
                custom_form_controls.append(ft.Divider())
                custom_form_controls.append(manage_row_editor)
            else:
                manage_row_editor = None

            manage_dynamic_form = DynamicForm(field_mappings, manage_current_json, on_manage_form_change, custom_controls=custom_form_controls)
            manage_form_container.controls = manage_dynamic_form.build()

            manage_json_editor = JSONEditor(manage_current_json, read_only=True)
            manage_json_container.content = manage_json_editor.build()

            manage_preview_container.content = build_manage_preview(manage_current_json)

            _set_status("✅ Template loaded. Edit fields to modify JSON, then click 'Update Template' to save to database.")
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_template(e):
        """Save template changes to local database only."""
        nonlocal manage_current_json, manage_dynamic_form

        if not edit_class_id_field.value:
            _set_status("❌ No template loaded", "red"); page.update(); return
        if not manage_dynamic_form:
            _set_status("❌ No form data available. Please load a template first.", "red"); page.update(); return

        _set_status("⏳ Saving template to local database...", "blue"); page.update()
        try:
            updated_json = manage_dynamic_form.get_json_data()
            extras = {}
            if manage_current_class_type == "Generic":
                extras["multiple_devices_allowed"] = updated_json.get("multiple_devices_allowed")
                extras["view_unlock_requirement"] = updated_json.get("view_unlock_requirement")
                extras["enable_smart_tap"] = updated_json.get("enable_smart_tap")
                extras["text_module_rows"] = updated_json.get("text_module_rows", [])

            response = api_client.update_class(
                class_id=edit_class_id_field.value,
                class_type=edit_class_type_field.value,
                class_json=updated_json,
                sync_to_google=False,
                **extras
            )
            _set_status(response.get("message", "✅ Template saved to local database!"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def insert_to_google_handler(e):
        """Sync template to Google Wallet API and trigger push notifications."""
        nonlocal manage_current_json, manage_dynamic_form

        if not edit_class_id_field.value:
            _set_status("❌ No template loaded", "red"); page.update(); return
        if not manage_dynamic_form:
            _set_status("❌ No form data available. Please load a template first.", "red"); page.update(); return

        _set_status("⏳ Syncing template to Google Wallet...", "blue"); page.update()
        try:
            updated_json = manage_dynamic_form.get_json_data()
            notification_body = notification_message_field.value.strip() if notification_message_field.value else None
            extras = {}
            if manage_current_class_type == "Generic":
                extras["multiple_devices_allowed"] = updated_json.get("multiple_devices_allowed")
                extras["view_unlock_requirement"] = updated_json.get("view_unlock_requirement")
                extras["enable_smart_tap"] = updated_json.get("enable_smart_tap")
                extras["text_module_rows"] = updated_json.get("text_module_rows", [])

            response = api_client.update_class(
                class_id=edit_class_id_field.value,
                class_type=edit_class_type_field.value,
                class_json=updated_json,
                sync_to_google=True,
                notification_message=notification_body,
                **extras
            )
            _set_status(response.get("message", "✅ Template synced to Google Wallet!"))
            notification_message_field.value = ""
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    # ── Startup ──
    startup_sync_classes()
    load_template_classes()

    left_panel.content = ft.Column([
                    ft.Text("Manage Templates", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("Select, preview, and edit your pass templates", size=11, color="grey"),
                    ft.Divider(),
                    ft.Container(height=10),
                    manage_templates_dropdown,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Show", icon="visibility", on_click=show_template,
                        style=ft.ButtonStyle(bgcolor="green", color="white"),
                    ),
                    ft.Divider(height=20),
                    ft.Text("Template Details", size=16, weight=ft.FontWeight.BOLD),
                    edit_class_id_field,
                    edit_class_type_field,
                    ft.Container(height=5),
                    ft.Text("Editable Fields", size=14, weight=ft.FontWeight.W_500, color="grey700"),
                    manage_form_container,
                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        "Update Template", icon="save", on_click=update_template, width=350,
                        style=ft.ButtonStyle(bgcolor="orange", color="white"),
                    ),
                    ft.Container(height=10),
                    ft.Text("Push Notification", size=14, weight=ft.FontWeight.W_500, color="grey700"),
                    notification_message_field,
                    ft.Container(height=5),
                    ft.ElevatedButton(
                        "Insert to Google Wallet", icon="cloud_upload",
                        on_click=insert_to_google_handler, width=350,
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
                    ft.Text("JSON Configuration", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Complete class JSON", size=10, color="grey"),
                    ft.Container(height=10),
                    manage_json_container,
                ], scroll="auto"),
                padding=15, bgcolor="grey50",
            ),
            # Right Panel: Live Preview
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text("Visual Preview", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("How your pass will look", size=10, color="grey"),
                    ft.Container(height=20),
                    manage_preview_container,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, bgcolor="grey100",
            ),
        ], expand=True, spacing=0),
        expand=True,
    )
