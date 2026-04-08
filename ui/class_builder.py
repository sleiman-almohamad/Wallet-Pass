"""
Template Builder Module - Complete Redesign
Dynamic class creation with JSON templates, form generation, and live preview
"""

import flet as ft
from core.json_templates import JSONTemplateManager, get_template, get_editable_fields
from ui.components.json_form_mapper import DynamicForm, set_nested_value
from ui.components.text_module_row_editor import TextModuleRowEditor
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR
import configs
import json


def create_template_builder(page, state, api_client=None):
    """
    Create the redesigned template builder interface with:
    - Left panel: Class ID, Type selector, Dynamic form
    - Middle panel: JSON preview
    - Right panel: Visual preview
    """
    
    # State variables
    current_class_id = None
    current_class_type = "Generic"
    current_json = {}
    dynamic_form = None
    row_editor = None
    
    # Left panel reference for resizing
    left_panel = ft.Container(
        expand=True,
        padding=15,
        bgcolor="white"
    )
    
    # UI References
    class_id_input_ref = ft.Ref[ft.TextField]()
    class_type_dropdown_ref = ft.Ref[ft.Dropdown]()
    form_container_ref = ft.Ref[ft.Column]()
    status_text_ref = ft.Ref[ft.Text]()
    
    def on_json_change(updated_json: dict):
        """Callback when JSON data changes from form"""
        nonlocal current_json
        current_json = updated_json
        page.update()
    
    def on_class_type_change(e):
        """When class type changes, load new template"""
        nonlocal current_class_type, current_json, dynamic_form
        
        current_class_type = e.control.value
        class_id = class_id_input_ref.current.value
        
        if not class_id:
            status_text_ref.current.value = state.t("msg.enter_class_id")
            status_text_ref.current.color = "orange"
            page.update()
            return
        
        # Load template for this class type
        current_json = get_template(current_class_type, class_id)
        
        # Get editable fields for this type
        field_mappings = get_editable_fields(current_class_type)
        
        # Create dynamic form (conditionally inject text modules for Generic)
        nonlocal row_editor
        custom_form_controls = []
        
        if current_class_type == "Generic":
            def on_rows_change(rows):
                nonlocal current_json
                current_json["text_module_rows"] = rows
                on_json_change(current_json)
                
            # Initialize with existing rows if present
            initial_rows = current_json.get("text_module_rows", [])
            row_editor = TextModuleRowEditor(initial_rows, on_change=on_rows_change, state=state, mode="class")
            custom_form_controls.append(ft.Divider())
            custom_form_controls.append(row_editor)
        else:
            row_editor = None
         # Create dynamic form
        dynamic_form = DynamicForm(
            field_mappings=field_mappings, # Changed from editable_fields to field_mappings
            initial_json=current_json,
            state=state,
            on_change_callback=on_json_change # Changed from on_form_change to on_json_change
        )
        form_controls = dynamic_form.build()
        
        # Update form container
        if form_container_ref.current:
            form_container_ref.current.controls = form_controls
        
        status_text_ref.current.value = state.t("msg.loaded_template_type", type=current_class_type)
        status_text_ref.current.color = "green"
        page.update()
    
    def on_class_id_change(e):
        """When class ID changes, update JSON"""
        nonlocal current_json
        
        class_id = e.control.value
        if class_id and current_json:
            # Update ID in JSON
            full_id = f"{configs.ISSUER_ID}.{class_id}" if not class_id.startswith(configs.ISSUER_ID) else class_id
            current_json["id"] = full_id
            
            # Trigger updates
            on_json_change(current_json)
    
    def save_template(e):
        """Save template to database"""
        nonlocal current_json
        
        class_id = class_id_input_ref.current.value
        
        if not class_id:
            status_text_ref.current.value = state.t("msg.class_id_req")
            status_text_ref.current.color = "red"
            page.update()
            return
        
        if not current_json:
            status_text_ref.current.value = state.t("msg.no_template_data")
            status_text_ref.current.color = "red"
            page.update()
            return
        
        status_text_ref.current.value = state.t("msg.saving_template")
        status_text_ref.current.color = "blue"
        page.update()
        
        try:
            if api_client:
                # Check if class already exists
                existing_class = api_client.get_class(class_id)
                
                
                # Extract extended generic fields from the form's current state
                form_data = dynamic_form.get_json_data() if dynamic_form else current_json
                extras = {"text_module_rows": form_data.get("text_module_rows", [])}

                if existing_class:
                    # Update existing class
                    print(f"Class '{class_id}' already exists, updating...")
                    result = api_client.update_class(
                        class_id=class_id,
                        class_type=current_class_type,
                        class_json=current_json,
                        **extras
                    )
                    status_text_ref.current.value = "✅ Template updated"
                    msg = state.t("msg.template_updated", id=class_id)
                else:
                    # Create new class
                    print(f"Creating new class '{class_id}'...")
                    result = api_client.create_class(
                        class_id=class_id,
                        class_type=current_class_type,
                        class_json=current_json,
                        **extras
                    )
                    status_text_ref.current.value = "✅ Template created"
                    msg = state.t("msg.template_created", id=class_id)
                
                # --- Success Dialog ---
                def dialog_dismissed(e):
                    reset_form(None)

                def close_dlg(e):
                    page.close(succ_dlg)

                succ_dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("✅ Success", weight=ft.FontWeight.BOLD),
                    content=ft.Text(msg, size=13),
                    on_dismiss=dialog_dismissed,
                    actions=[
                        ft.TextButton("Close", on_click=close_dlg),
                    ],
                )
                page.open(succ_dlg)
                
                # Refresh other views that depend on the template list
                if state:
                    state.refresh_ui("pass_generator_templates")
                    state.refresh_ui("manage_templates_list")
                    state.refresh_ui("manage_passes_list")
                    state.refresh_ui("send_notification_list")
            else:
                status_text_ref.current.value = state.t("msg.api_not_connected")
                status_text_ref.current.color = "orange"
        except Exception as ex:
            print(f"Error saving template: {ex}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a 409 conflict error
            error_msg = str(ex)
            if "409" in error_msg or "Conflict" in error_msg:
                status_text_ref.current.value = state.t("msg.class_exists_err", id=class_id)
            else:
                status_text_ref.current.value = f"❌ Error: {str(ex)}"
            status_text_ref.current.color = "red"
        
        page.update()
    
    def reset_form(e):
        """Reset the form"""
        nonlocal current_json, dynamic_form
        
        class_id_input_ref.current.value = ""
        class_type_dropdown_ref.current.value = "Generic"
        current_json = {}
        
        if form_container_ref.current:
            form_container_ref.current.controls = []
        
        status_text_ref.current.value = ""
        page.update()
    
    # Build the UI
    left_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR,
        content=ft.Column([
            ft.Text("Create New Template", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Define a unique Class ID to begin crafting your digital wallet experience.", color=TEXT_SECONDARY, size=13),
            ft.Container(height=8),
            
            card(ft.Column([
                section_title("Class Configuration", ft.Icons.STYLE),
                ft.TextField(
                    ref=class_id_input_ref,
                    label="Class ID *",
                    hint_text="e.g., coffee_loyalty_2025",
                    width=380, border_radius=8, text_size=13,
                    on_change=on_class_id_change
                ),
                ft.Dropdown(
                    ref=class_type_dropdown_ref,
                    label="Pass Type",
                    value="Generic",
                    width=380, border_radius=8, text_size=13,
                    options=[
                        ft.dropdown.Option("Generic"),
                        ft.dropdown.Option("LoyaltyCard"),
                        ft.dropdown.Option("GiftCard"),
                        ft.dropdown.Option("EventTicket"),
                        ft.dropdown.Option("TransitPass")
                    ],
                    on_change=on_class_type_change
                ),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "Create Template",
                    icon=ft.Icons.ADD_CIRCLE,
                    on_click=save_template,
                    bgcolor=PRIMARY, color="white", height=40, width=200,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.Text(ref=status_text_ref, value="", size=12),
            ], spacing=12)),
            
            ft.Container(height=8),
            
            card(ft.Column([
                section_title("Template Fields", ft.Icons.TUNE),
                ft.Text("Dynamic configuration fields based on pass type", size=11, color=TEXT_SECONDARY),
                ft.Column(
                    ref=form_container_ref,
                    controls=[],
                    scroll="auto",
                    spacing=12
                ),
                ft.Divider(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        "Update & Sync Template",
                        icon="sync",
                        on_click=save_template,
                        bgcolor="blue", color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.OutlinedButton("Reset Form", icon="refresh", on_click=reset_form,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], spacing=10),
            ], spacing=12)),
            
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    )
    
    return ft.Container(
        content=left_panel,
        expand=True,
        padding=15,
        bgcolor="white"
    )
