"""
Template Builder Module - Complete Redesign
Dynamic class creation with JSON templates, form generation, and live preview
"""

import flet as ft
from json_templates import JSONTemplateManager, get_template, get_editable_fields
from ui.components.json_form_mapper import DynamicForm, set_nested_value
from ui.components.json_editor import JSONEditor
import configs
import json


def create_template_builder(page, api_client=None):
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
    
    # UI References
    class_id_input_ref = ft.Ref[ft.TextField]()
    class_type_dropdown_ref = ft.Ref[ft.Dropdown]()
    form_container_ref = ft.Ref[ft.Column]()
    json_container_ref = ft.Ref[ft.Container]()
    preview_container_ref = ft.Ref[ft.Container]()
    status_text_ref = ft.Ref[ft.Text]()
    
    def build_visual_preview(json_data: dict) -> ft.Container:
        """Build visual pass preview from JSON data"""
        # Extract visual elements based on class type
        bg_color = json_data.get("hexBackgroundColor", "#4285f4")
        
        # Get logo URL (different paths for different types)
        logo_url = None
        if "programLogo" in json_data:
            logo_url = json_data.get("programLogo", {}).get("sourceUri", {}).get("uri")
        elif "logo" in json_data:
            logo_url = json_data.get("logo", {}).get("sourceUri", {}).get("uri")
        
        # Get hero image URL
        hero_url = None
        if "heroImage" in json_data:
            hero_url = json_data.get("heroImage", {}).get("sourceUri", {}).get("uri")
        
        # Get header/title text
        header_text = "Business Name"
        card_title = "Pass Title"
        
        if "localizedIssuerName" in json_data:
            header_text = json_data.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
        elif "issuerName" in json_data:
            header_text = json_data.get("issuerName", "Business")
        
        if "localizedProgramName" in json_data:
            card_title = json_data.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
        elif "eventName" in json_data:
            card_title = json_data.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
        elif "header" in json_data:
            header_text = json_data.get("header", {}).get("defaultValue", {}).get("value", "Header")
        if "cardTitle" in json_data:
            card_title = json_data.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")
        
        # Build logo control
        if logo_url:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(src=logo_url, width=50, height=50, fit=ft.ImageFit.COVER)
            )
        else:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25, bgcolor="white30",
                content=ft.Icon("business", color="white", size=30),
                alignment=ft.alignment.center
            )
        
        # Build hero image control
        if hero_url:
            hero_control = ft.Container(
                height=150,
                content=ft.Image(src=hero_url, width=300, height=150, fit=ft.ImageFit.COVER)
            )
        else:
            hero_control = ft.Container(
                height=150, bgcolor="black12",
                content=ft.Column([
                    ft.Icon("image", size=40, color="grey"),
                    ft.Text("Hero Image", size=12, color="grey")
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        
        # Build the pass preview
        return ft.Container(
            width=300,
            bgcolor=bg_color,
            border_radius=15,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=15, color="black26", offset=ft.Offset(0, 5)),
            content=ft.Column([
                # Top: Logo & Header
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        logo_control,
                        ft.Container(width=10),
                        ft.Text(header_text, color="white", weight=ft.FontWeight.BOLD, size=14, expand=True)
                    ])
                ),
                # Card Title
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(card_title, color="white", size=20, weight=ft.FontWeight.BOLD)
                ),
                # Hero Image
                hero_control,
                # Bottom: QR & Details
                ft.Container(
                    bgcolor="white",
                    padding=15,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=11),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Container(
                                width=70, height=70, bgcolor="grey200", border_radius=5,
                                content=ft.Icon("qr_code_2", size=50, color="grey"),
                                alignment=ft.alignment.center
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text("Sample User", weight=ft.FontWeight.BOLD, size=13, color="black"),
                                ft.Text("ID: 1234567890", size=11, color="grey")
                            ])
                        ])
                    ])
                )
            ], spacing=0)
        )
    
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
            status_text_ref.current.value = "⚠️ Please enter a Class ID first"
            status_text_ref.current.color = "orange"
            page.update()
            return
        
        # Load template for this class type
        current_json = get_template(current_class_type, class_id)
        
        # Get editable fields for this type
        field_mappings = get_editable_fields(current_class_type)
        
        # Create dynamic form
        dynamic_form = DynamicForm(field_mappings, current_json, on_json_change)
        form_controls = dynamic_form.build()
        
        # Update form container
        if form_container_ref.current:
            form_container_ref.current.controls = form_controls
        
        # Create/update JSON editor
        json_editor = JSONEditor(current_json, on_change=on_json_change, read_only=True)
        if json_container_ref.current:
            json_container_ref.current.content = json_editor.build()
        
        # Update preview
        if preview_container_ref.current:
            preview_container_ref.current.content = build_visual_preview(current_json)
        
        status_text_ref.current.value = f"✓ Loaded {current_class_type} template"
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
            status_text_ref.current.value = "❌ Class ID is required"
            status_text_ref.current.color = "red"
            page.update()
            return
        
        if not current_json:
            status_text_ref.current.value = "❌ No template data to save"
            status_text_ref.current.color = "red"
            page.update()
            return
        
        status_text_ref.current.value = "⏳ Saving template..."
        status_text_ref.current.color = "blue"
        page.update()
        
        try:
            if api_client:
                # Check if class already exists
                existing_class = api_client.get_class(class_id)
                
                if existing_class:
                    # Update existing class
                    print(f"Class '{class_id}' already exists, updating...")
                    result = api_client.update_class(
                        class_id=class_id,
                        class_type=current_class_type,
                        class_json=current_json
                    )
                    status_text_ref.current.value = f"✅ Template '{class_id}' updated successfully!"
                else:
                    # Create new class
                    print(f"Creating new class '{class_id}'...")
                    result = api_client.create_class(
                        class_id=class_id,
                        class_type=current_class_type,
                        class_json=current_json
                    )
                    status_text_ref.current.value = f"✅ Template '{class_id}' created successfully!"
                
                status_text_ref.current.color = "green"
            else:
                status_text_ref.current.value = "⚠️ API client not connected"
                status_text_ref.current.color = "orange"
        except Exception as ex:
            print(f"Error saving template: {ex}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a 409 conflict error
            error_msg = str(ex)
            if "409" in error_msg or "Conflict" in error_msg:
                status_text_ref.current.value = f"❌ Class '{class_id}' already exists. Try refreshing and editing it instead."
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
            json_container_ref.current.content = ft.Text("Select a class type to begin", color="grey")
        
        if preview_container_ref.current:
            preview_container_ref.current.content = ft.Column([
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text("Preview", size=12, color="grey")
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        status_text_ref.current.value = ""
        page.update()
    
    # Build the UI
    return ft.Row([
        # LEFT PANEL: Form
        ft.Container(
            width=380,
            content=ft.Column([
                ft.Text("Create Pass Class", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Dynamic class creation with templates", size=11, color="grey"),
                ft.Divider(),
                
                ft.Text("Basic Information", size=16, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    ref=class_id_input_ref,
                    label="Class ID *",
                    hint_text="e.g., coffee_loyalty_2025",
                    width=350,
                    on_change=on_class_id_change
                ),
                ft.Dropdown(
                    ref=class_type_dropdown_ref,
                    label="Class Type *",
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
                
                ft.Text("Template Fields", size=16, weight=ft.FontWeight.BOLD),
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
                        "Save Template",
                        icon="save",
                        on_click=save_template,
                        style=ft.ButtonStyle(bgcolor="blue", color="white")
                    ),
                    ft.OutlinedButton("Reset", icon="refresh", on_click=reset_form)
                ], spacing=10),
                
                ft.Text(ref=status_text_ref, value="", size=11),
                
            ], spacing=8, scroll="auto"),
            padding=15,
            bgcolor="white"
        ),
        
        # MIDDLE PANEL: JSON Preview
        ft.Container(
            width=320,
            content=ft.Column([
                ft.Text("JSON Configuration", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Live JSON preview", size=10, color="grey"),
                ft.Container(height=10),
                ft.Container(
                    ref=json_container_ref,
                    content=ft.Text("Select a class type to see JSON", color="grey", size=11),
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
                ft.Text("Visual Preview", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("How your pass will look", size=10, color="grey"),
                ft.Container(height=20),
                ft.Container(
                    ref=preview_container_ref,
                    content=ft.Column([
                        ft.Icon("credit_card", size=80, color="grey300"),
                        ft.Text("Preview will appear here", size=12, color="grey")
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
