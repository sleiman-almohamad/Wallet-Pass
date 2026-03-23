"""
Template Builder Module - Complete Redesign
Dynamic class creation with JSON templates, form generation, and live preview
"""

import flet as ft
from core.json_templates import JSONTemplateManager, get_template, get_editable_fields
from ui.components.json_form_mapper import DynamicForm, set_nested_value
from ui.components.json_editor import JSONEditor
from ui.components.text_module_row_editor import TextModuleRowEditor
from ui.components.preview_builder import build_comprehensive_preview
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
    json_editor = None
    row_editor = None
    
    # Left panel reference for resizing
    left_panel = ft.Container(
        width=420,
        padding=15,
        bgcolor="white"
    )
    
    # UI References
    class_id_input_ref = ft.Ref[ft.TextField]()
    class_type_dropdown_ref = ft.Ref[ft.Dropdown]()
    form_container_ref = ft.Ref[ft.Column]()
    json_container_ref = ft.Ref[ft.Container]()
    preview_container_ref = ft.Ref[ft.Container]()
    status_text_ref = ft.Ref[ft.Text]()
    
    def build_visual_preview(json_data: dict) -> ft.Container:
        """Build visual pass preview from JSON data using centralized builder"""
        return build_comprehensive_preview(json_data, state=state)
    
    def on_json_change(updated_json: dict):
        """Callback when JSON data changes from form or editor"""
        nonlocal current_json
        current_json = updated_json
        
        # Update JSON editor
        if json_editor:
            json_editor.update_json(updated_json)
        
        # Update visual preview
        if preview_container_ref.current:
            preview_container_ref.current.content = build_visual_preview(updated_json)
        
        page.update()
    
    def on_class_type_change(e):
        """When class type changes, load new template"""
        nonlocal current_class_type, current_json, dynamic_form, json_editor
        
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
        
        # Create/update JSON editor
        json_editor = JSONEditor(current_json, state=state, on_change=on_json_change, read_only=True)
        if json_container_ref.current:
            json_container_ref.current.content = json_editor.build()
        
        # Update preview
        if preview_container_ref.current:
            preview_container_ref.current.content = build_visual_preview(current_json)
        
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
                    status_text_ref.current.value = state.t("msg.template_updated", id=class_id)
                else:
                    # Create new class
                    print(f"Creating new class '{class_id}'...")
                    result = api_client.create_class(
                        class_id=class_id,
                        class_type=current_class_type,
                        class_json=current_json,
                        **extras
                    )
                    status_text_ref.current.value = state.t("msg.template_created", id=class_id)
                
                status_text_ref.current.color = "green"
                
                # Refresh other views that depend on the template list
                if state:
                    state.refresh_ui("pass_generator_templates")
                    state.refresh_ui("manage_templates_list")
                    state.refresh_ui("manage_passes_list")
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
        nonlocal current_json, dynamic_form, json_editor
        
        class_id_input_ref.current.value = ""
        class_type_dropdown_ref.current.value = "Generic"
        current_json = {}
        
        if form_container_ref.current:
            form_container_ref.current.controls = []
        
        if json_container_ref.current:
            json_container_ref.current.content = ft.Text(state.t("msg.select_type_hint"), color="grey")
        
        if preview_container_ref.current:
            preview_container_ref.current.content = ft.Column([
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text(state.t("label.visual_preview"), size=12, color="grey")
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        status_text_ref.current.value = ""
        page.update()
    
    # Build the UI
    left_panel = ft.Container(
        width=420,
        content=ft.Column([
            ft.Text(state.t("header.template_builder"), size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.template_builder"), size=11, color="grey"),
            ft.Divider(),
            
            ft.Text(state.t("label.basic_info"), size=16, weight=ft.FontWeight.BOLD),
            ft.TextField(
                ref=class_id_input_ref,
                label=state.t("label.class_id_req"),
                hint_text="e.g., coffee_loyalty_2025",
                width=350,
                on_change=on_class_id_change
            ),
            ft.Dropdown(
                ref=class_type_dropdown_ref,
                label=state.t("label.class_type_req"),
                value="Generic",
                width=350,
                options=[
                    ft.dropdown.Option("Generic"),
                    ft.dropdown.Option("LoyaltyCard"),
                    ft.dropdown.Option("GiftCard"),
                    ft.dropdown.Option("EventTicket"),
                    ft.dropdown.Option("TransitPass")
                ],
                on_change=on_class_type_change
            ),
            
            ft.Divider(height=15),
            
            ft.Text(state.t("label.template_fields"), size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Fields will appear here after selecting a type", size=10, color="grey"),
            
            ft.Column(
                ref=form_container_ref,
                controls=[],
                scroll="auto",
                spacing=8
            ),
            
            ft.Divider(height=15),
            
            ft.Row([
                ft.ElevatedButton(
                    state.t("btn.update_template"),
                    icon="save",
                    on_click=save_template,
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                ft.OutlinedButton(state.t("btn.reset"), icon="refresh", on_click=reset_form)
            ], spacing=10),
            
            
            ft.Text(ref=status_text_ref, value="", size=11),
            
        ], spacing=8, scroll="auto")
    )
    
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

    return ft.Row([
        # LEFT PANEL: Form Inputs
            left_panel,
            splitter,
            
            # MIDDLE PANEL: JSON Preview
        ft.Container(
            width=320,
            content=ft.Column([
                ft.Text(state.t("label.json_config"), size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Live JSON preview", size=10, color="grey"),
                ft.Container(height=10),
                ft.Container(
                    ref=json_container_ref,
                    content=ft.Text(state.t("msg.select_type_hint"), color="grey", size=11),
                    expand=True
                )
            ], scroll="auto"),
            padding=15,
            bgcolor="grey50"
        ),
        
        # RIGHT PANEL: Visual Preview
        ft.Container(
            expand=True,
            content=ft.Column([
                ft.Text(state.t("label.visual_preview"), size=18, weight=ft.FontWeight.BOLD),
                ft.Text("How your pass will look", size=10, color="grey"),
                ft.Container(height=20),
                ft.Container(
                    ref=preview_container_ref,
                    content=ft.Column([
                        ft.Icon("credit_card", size=80, color="grey300"),
                        ft.Text(state.t("msg.preview_hint"), size=12, color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.top_center,
                    expand=True
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor="grey100"
        )
    ], expand=True, spacing=0)
