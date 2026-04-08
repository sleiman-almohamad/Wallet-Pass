"""
Manage Templates View
Extracted from main.py — 3-panel layout for managing Google Wallet template classes.
"""

import flet as ft
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
from core.json_templates import get_editable_fields
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR
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
    manage_dynamic_form = None
    manage_current_json = {}
    manage_current_class_type = None
    manage_row_editor = None

    # Main container
    main_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR
    )

    # ── UI Controls ──
    manage_templates_dropdown = ft.Dropdown(
        label="Select Class ID",
        width=380, border_radius=8, text_size=13,
        options=[],
        on_change=lambda e: show_template(e)
    )

    manage_status = ft.Text("", size=12)

    manage_form_container = ft.Column(
        controls=[ft.Text("Select a Class ID above to load text modules.", color=TEXT_SECONDARY, size=11)],
        spacing=8,
        scroll="auto",
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
                
                # Auto-load the template for the first selected class to prevent empty state
                show_template(None)
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
            
    # Register this function for remote refresh
    state.register_refresh_callback("manage_templates_list", load_template_classes)

    def show_template(e):
        """Fetch and display template for editing from local database."""
        nonlocal manage_current_json, manage_current_class_type, manage_dynamic_form

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
                # Generic class: We want to keep text_module_rows if they exist in class_data
                # so they can be edited as the 'Blueprint'.
                # Branding still usually belongs to the pass, but the layout is defined here.
                if class_data.get("text_module_rows"):
                    json_data["text_module_rows"] = class_data["text_module_rows"]

            manage_current_json = json_data.copy()
            manage_current_class_type = class_type

            field_mappings = get_editable_fields(class_type)

            def on_manage_form_change(updated_json):
                nonlocal manage_current_json
                manage_current_json = updated_json
                page.update()

            custom_form_controls = []
            nonlocal manage_row_editor

            if class_type == "Generic":
                # Generic classes now use the Row Editor to define the Blueprint (Headers).
                initial_rows = json_data.get("text_module_rows", [])
                manage_row_editor = TextModuleRowEditor(initial_rows, state=state, mode="class")
                
                custom_form_controls.append(manage_row_editor)
            else:
                manage_row_editor = None

            manage_dynamic_form = DynamicForm(field_mappings, manage_current_json, state=state, on_change_callback=on_manage_form_change, custom_controls=custom_form_controls)
            manage_form_container.controls = manage_dynamic_form.build()

            _set_status(state.t("msg.template_loaded"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        if manage_form_container.page:
            manage_form_container.update()
        if manage_status.page:
            manage_status.update()
        page.update()

    def update_and_sync_handler(e):
        """Save template changes to local database AND sync to Google Wallet."""
        nonlocal manage_current_json, manage_dynamic_form, manage_row_editor

        if not manage_templates_dropdown.value:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return
        if not manage_dynamic_form:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return

        _set_status("⏳ Updating locally and syncing to Google...", "blue"); page.update()
        try:
            updated_json = manage_dynamic_form.get_json_data()
            extras = {}

            # Perform the update with sync_to_google=True
            response = api_client.update_class(
                class_id=manage_templates_dropdown.value,
                class_type=manage_current_class_type,
                class_json=updated_json,
                text_module_rows=manage_row_editor.get_rows() if manage_row_editor else [],
                sync_to_google=True,
                **extras
            )
            # --- Success Dialog ---
            def close_dlg(e):
                page.close(save_dlg)

            save_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Template Saved Successfully!", weight=ft.FontWeight.BOLD),
                content=ft.Text("The template has been updated locally and synced to Google Wallet.", size=13),
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(save_dlg)

            # Refresh other views
            if state:
                state.refresh_ui("pass_generator_templates")
                state.refresh_ui("manage_templates_list")
                state.refresh_ui("manage_passes_list")
                state.refresh_ui("send_notification_list")
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    # ── Startup ──
    load_template_classes()

    main_panel.content = ft.Column([
        ft.Text("Manage Templates", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
        ft.Text("Edit Text Module Rows for an existing Class.", color=TEXT_SECONDARY, size=13),
        ft.Container(height=8),
        manage_templates_dropdown,
        ft.Container(height=8),
        
        card(ft.Column([
            section_title("Text Module Rows", ft.Icons.TABLE_CHART),
            ft.Container(manage_form_container, padding=ft.padding.only(left=8)),
            manage_status
        ], spacing=12)),
        
        ft.Container(
            content=ft.ElevatedButton(
                "Save Template",
                icon=ft.Icons.SAVE,
                on_click=update_and_sync_handler,
                bgcolor=PRIMARY, color="white", height=40, width=180,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            alignment=ft.alignment.center_right
        )
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    return ft.Container(
        content=main_panel,
        expand=True,
        bgcolor=BG_COLOR
    )
