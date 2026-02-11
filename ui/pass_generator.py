"""
Pass Generator UI
Creates individual Google Wallet passes for end users
"""

import flet as ft
from typing import Dict, List, Any, Optional
from qr_generator import generate_qr_code


# Field configurations for each pass type
PASS_TYPE_FIELDS = {
    "Generic": [
        {"name": "header_value", "label": "Header Value", "type": "text", "hint": "e.g., VIP Member"},
        {"name": "subheader", "label": "Subheader", "type": "text", "hint": "e.g., Premium Access"},
    ],
    "EventTicket": [
        {"name": "event_name", "label": "Event Name", "type": "text", "hint": "e.g., Concert 2024"},
        {"name": "event_date", "label": "Event Date", "type": "text", "hint": "e.g., 2024-12-25"},
        {"name": "event_time", "label": "Event Time", "type": "text", "hint": "e.g., 19:00"},
        {"name": "seat_number", "label": "Seat Number", "type": "text", "hint": "e.g., A12"},
        {"name": "section", "label": "Section", "type": "text", "hint": "e.g., Lower Bowl"},
        {"name": "gate", "label": "Gate", "type": "text", "hint": "e.g., Gate 3"},
    ],
    "LoyaltyCard": [
        {"name": "points_balance", "label": "Points Balance", "type": "number", "hint": "e.g., 1500"},
        {"name": "tier_level", "label": "Tier Level", "type": "text", "hint": "e.g., Gold"},
        {"name": "member_since", "label": "Member Since", "type": "text", "hint": "e.g., 2024-01-15"},
        {"name": "rewards_available", "label": "Rewards Available", "type": "number", "hint": "e.g., 3"},
    ],
    "GiftCard": [
        {"name": "balance", "label": "Card Balance", "type": "number", "hint": "e.g., 50.00"},
        {"name": "card_number", "label": "Card Number", "type": "text", "hint": "e.g., 1234-5678-9012"},
        {"name": "expiry_date", "label": "Expiry Date", "type": "text", "hint": "e.g., 2025-12-31"},
    ],
    "TransitPass": [
        {"name": "pass_type", "label": "Pass Type", "type": "text", "hint": "e.g., Monthly Pass"},
        {"name": "valid_from", "label": "Valid From", "type": "text", "hint": "e.g., 2024-12-01"},
        {"name": "valid_until", "label": "Valid Until", "type": "text", "hint": "e.g., 2024-12-31"},
        {"name": "zones", "label": "Zones", "type": "text", "hint": "e.g., Zone 1-3"},
    ],
}


def create_pass_generator(page: ft.Page, api_client, wallet_client):
    """
    Create the Pass Generator tab UI
    
    Args:
        page: Flet page instance
        api_client: API client for database operations
        wallet_client: Google Wallet client for pass generation
    """
    
    # Refs for form controls
    template_dropdown_ref = ft.Ref[ft.Dropdown]()
    holder_name_ref = ft.Ref[ft.TextField]()
    holder_email_ref = ft.Ref[ft.TextField]()
    status_ref = ft.Ref[ft.Text]()
    result_container_ref = ft.Ref[ft.Container]()
    
    # Container for dynamic fields
    dynamic_fields_container = ft.Column(spacing=10)
    dynamic_field_refs = {}  # Store refs for dynamic fields
    
    # Preview container
    preview_container = ft.Container(
        content=ft.Text("Select a template to see preview", color="grey"),
        alignment=ft.alignment.center,
        padding=20
    )
    
    # Current selected class data
    current_class_data = {"class_type": None}
    
    def build_preview(class_data: Dict, pass_data: Dict):
        """Build visual pass preview"""
        bg_color = class_data.get("base_color", "#4285f4")
        logo_url = class_data.get("logo_url")
        header_text = class_data.get("header_text", "Business Name")
        card_title = class_data.get("card_title", "Pass Title")
        holder_name = pass_data.get("holder_name", "John Doe")
        
        # Logo
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
        
        # Build detail text based on pass type
        detail_lines = []
        class_type = class_data.get("class_type", "Generic")
        
        if class_type == "EventTicket":
            detail_lines.append(f"Event: {pass_data.get('event_name', 'TBD')}")
            detail_lines.append(f"Date: {pass_data.get('event_date', 'TBD')}")
            detail_lines.append(f"Seat: {pass_data.get('seat_number', 'TBD')}")
        elif class_type == "LoyaltyCard":
            detail_lines.append(f"Points: {pass_data.get('points_balance', '0')}")
            detail_lines.append(f"Tier: {pass_data.get('tier_level', 'Standard')}")
        elif class_type == "GiftCard":
            detail_lines.append(f"Balance: ${pass_data.get('balance', '0.00')}")
            detail_lines.append(f"Card: {pass_data.get('card_number', 'XXXX-XXXX')}")
        elif class_type == "TransitPass":
            detail_lines.append(f"Type: {pass_data.get('pass_type', 'Standard')}")
            detail_lines.append(f"Valid: {pass_data.get('valid_from', 'TBD')} - {pass_data.get('valid_until', 'TBD')}")
        else:
            detail_lines.append(f"Status: Active")
        
        return ft.Container(
            width=350,
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
                        ft.Text(header_text, color="white", weight=ft.FontWeight.BOLD, size=16, expand=True)
                    ])
                ),
                # Card Title
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(card_title, color="white", size=22, weight=ft.FontWeight.BOLD)
                ),
                # Hero Image placeholder
                ft.Container(
                    height=150, bgcolor="black12",
                    content=ft.Column([
                        ft.Icon("confirmation_number" if class_type == "EventTicket" else "card_giftcard", size=40, color="grey"),
                        ft.Text(class_type, size=12, color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                # Bottom: QR & Details
                ft.Container(
                    bgcolor="white",
                    padding=15,
                    content=ft.Column([
                        ft.Text("Pass Holder", color="grey", size=10),
                        ft.Text(holder_name, weight=ft.FontWeight.BOLD, size=16, color="black"),
                        ft.Container(height=10),
                        ft.Column([
                            ft.Text(line, size=12, color="grey") for line in detail_lines
                        ], spacing=3),
                        ft.Container(height=10),
                        ft.Container(
                            width=80, height=80, bgcolor="grey200", border_radius=5,
                            content=ft.Icon("qr_code_2", size=60, color="grey"),
                            alignment=ft.alignment.center
                        )
                    ])
                )
            ], spacing=0)
        )
    
    def update_preview():
        """Update preview based on current form values"""
        if not current_class_data.get("class_type"):
            return
        
        # Collect pass data from form
        pass_data = {
            "holder_name": holder_name_ref.current.value if holder_name_ref.current else "John Doe"
        }
        
        # Add dynamic field values
        for field_name, field_ref in dynamic_field_refs.items():
            if field_ref.current:
                pass_data[field_name] = field_ref.current.value or ""
        
        preview_container.content = build_preview(current_class_data, pass_data)
        page.update()
    
    def on_template_selected(e):
        """Handle template selection"""
        if not template_dropdown_ref.current.value:
            return
        
        try:
            # Get class_id
            class_id = template_dropdown_ref.current.value
            
            # Get class data from local database
            if class_id in class_metadata:
                class_data = class_metadata[class_id]
            else:
                # Fetch from database if not in metadata
                class_data = api_client.get_class(class_id) if api_client else None
                
                if not class_data:
                    status_ref.current.value = f"❌ Template '{class_id}' not found in database"
                    status_ref.current.color = "red"
                    page.update()
                    return
                
                # Store in metadata
                class_metadata[class_id] = class_data
            
            # Get class type
            class_type = class_data.get("class_type", "Generic")
            
            # Extract visual properties from class_json if available
            class_json = class_data.get("class_json", {})
            
            # Extract background color
            base_color = class_data.get("base_color") or class_json.get("hexBackgroundColor", "#4285f4")
            
            # Extract logo URL
            logo_url = class_data.get("logo_url")
            if not logo_url and "logo" in class_json:
                logo_url = class_json.get("logo", {}).get("sourceUri", {}).get("uri")
            elif not logo_url and "programLogo" in class_json:
                logo_url = class_json.get("programLogo", {}).get("sourceUri", {}).get("uri")
            
            # Extract header text
            header_text = class_data.get("header_text") or class_data.get("issuer_name", "Business Name")
            if not header_text or header_text == "Business Name":
                if "localizedIssuerName" in class_json:
                    header_text = class_json.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
                elif "issuerName" in class_json:
                    header_text = class_json.get("issuerName", "Business")
            
            # Extract card title
            card_title = class_data.get("card_title", "Pass Title")
            if not card_title or card_title == "Pass Title":
                if "localizedProgramName" in class_json:
                    card_title = class_json.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
                elif "eventName" in class_json:
                    card_title = class_json.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
                elif "cardTitle" in class_json:
                    card_title = class_json.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")
            
            # Store current class data for preview
            current_class_data.clear()
            current_class_data.update({
                "class_type": class_type,
                "class_id": class_id,
                "base_color": base_color,
                "logo_url": logo_url,
                "header_text": header_text,
                "card_title": card_title
            })
            
            # Clear dynamic fields
            dynamic_fields_container.controls.clear()
            dynamic_field_refs.clear()
            
            # Get field configuration for this type
            fields_config = PASS_TYPE_FIELDS.get(class_type, [])
            
            # Create dynamic fields
            for field_config in fields_config:
                field_ref = ft.Ref[ft.TextField]()
                dynamic_field_refs[field_config["name"]] = field_ref
                
                field = ft.TextField(
                    ref=field_ref,
                    label=field_config["label"],
                    hint_text=field_config["hint"],
                    width=400,
                    on_change=lambda e: update_preview()
                )
                
                dynamic_fields_container.controls.append(field)
            
            status_ref.current.value = f"✅ Template loaded from database: {class_type}"
            status_ref.current.color = "green"
            
            # Update preview
            update_preview()
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            status_ref.current.value = f"❌ Error: {str(ex)}"
            status_ref.current.color = "red"
        
        page.update()
    
    # Store class metadata (id -> full class info)
    class_metadata = {}
    
    def load_templates():
        """Load available templates into dropdown from local database"""
        try:
            # Fetch classes from local database via API
            classes = api_client.get_classes() if api_client else []
            
            if classes and len(classes) > 0:
                # Clear metadata
                class_metadata.clear()
                
                # Store metadata for each class
                for cls in classes:
                    class_metadata[cls["class_id"]] = cls
                
                template_dropdown_ref.current.options = [
                    ft.dropdown.Option(
                        key=cls["class_id"],
                        text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})"
                    )
                    for cls in classes
                ]
                status_ref.current.value = f"✅ Loaded {len(classes)} template(s) from local database"
                status_ref.current.color = "green"
            else:
                template_dropdown_ref.current.options = []
                status_ref.current.value = "ℹ️ No templates found. Create one in 'Template Builder' tab or restart app to sync from Google Wallet."
                status_ref.current.color = "blue"
            page.update()
        except Exception as e:
            status_ref.current.value = f"❌ Error loading templates: {e}"
            status_ref.current.color = "red"
            page.update()
    
    def generate_pass(e):
        """Generate the pass"""
        # Validate inputs
        if not template_dropdown_ref.current.value:
            status_ref.current.value = "❌ Please select a template"
            status_ref.current.color = "red"
            page.update()
            return
        
        if not holder_name_ref.current.value:
            status_ref.current.value = "❌ Please enter holder name"
            status_ref.current.color = "red"
            page.update()
            return
        
        if not holder_email_ref.current.value:
            status_ref.current.value = "❌ Please enter holder email"
            status_ref.current.color = "red"
            page.update()
            return
        
        status_ref.current.value = "⏳ Generating pass..."
        status_ref.current.color = "blue"
        page.update()
        
        try:
            # Collect pass data
            pass_data = {}
            for field_name, field_ref in dynamic_field_refs.items():
                if field_ref.current and field_ref.current.value:
                    pass_data[field_name] = field_ref.current.value
            
            # Generate unique object ID
            import time
            import configs
            timestamp = int(time.time())
            clean_name = holder_name_ref.current.value.replace(' ', '_').lower()
            object_suffix = f"pass_{timestamp}_{clean_name}"
            object_id = f"{configs.ISSUER_ID}.{object_suffix}"
            
            # Get class_id and ensure it has issuer prefix
            class_id = template_dropdown_ref.current.value
            if not class_id.startswith(configs.ISSUER_ID):
                class_id = f"{configs.ISSUER_ID}.{class_id}"
            
            # Get class type from current class data
            class_type = current_class_data.get("class_type", "Generic")
            
            # Build the appropriate pass object for Google Wallet
            if class_type == "EventTicket":
                google_pass_object = wallet_client.build_event_ticket_object(
                    object_id=object_id,
                    class_id=class_id,
                    holder_name=holder_name_ref.current.value,
                    holder_email=holder_email_ref.current.value,
                    pass_data=pass_data
                )
            elif class_type == "LoyaltyCard":
                google_pass_object = wallet_client.build_loyalty_object(
                    object_id=object_id,
                    class_id=class_id,
                    holder_name=holder_name_ref.current.value,
                    holder_email=holder_email_ref.current.value,
                    pass_data=pass_data
                )
            else:
                google_pass_object = wallet_client.build_generic_object(
                    object_id=object_id,
                    class_id=class_id,
                    holder_name=holder_name_ref.current.value,
                    holder_email=holder_email_ref.current.value,
                    pass_data=pass_data
                )
            
            # Create pass object in Google Wallet
            status_ref.current.value = "⏳ Creating pass in Google Wallet..."
            status_ref.current.color = "blue"
            page.update()
            
            wallet_result = wallet_client.create_pass_object(google_pass_object, class_type)
            
            # Generate JWT-signed save link
            save_link = wallet_client.generate_save_link(object_id, class_type)
            
            # Try to create pass in local database (optional - for record keeping)
            try:
                status_ref.current.value = "⏳ Saving to local database..."
                status_ref.current.color = "blue"
                page.update()
                
                # Strip issuer prefix from class_id for local database
                db_class_id = class_id.split('.')[-1] if '.' in class_id else class_id
                
                db_result = api_client.create_pass(
                    object_id=object_id,
                    class_id=db_class_id,
                    holder_name=holder_name_ref.current.value,
                    holder_email=holder_email_ref.current.value,
                    status="Active",
                    pass_data=pass_data
                )
                db_saved = True
            except Exception as db_error:
                # Local database save failed, but pass was still created in Google Wallet
                print(f"Warning: Could not save to local database: {db_error}")
                db_saved = False
            
            # Generate QR code for the save link
            status_ref.current.value = "⏳ Generating QR code..."
            status_ref.current.color = "blue"
            page.update()
            
            import time
            qr_filename = f"pass_qr_{int(time.time())}"
            qr_image_path = generate_qr_code(save_link, qr_filename)
            
            # Show success result with QR code
            result_container_ref.current.content = ft.Column([
                ft.Text("✅ Pass created successfully!", color="green", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                ft.Text(
                    f"{'✅ Saved to local database' if db_saved else '⚠️ Not saved to local database (class not in DB)'}",
                    size=10,
                    color="green" if db_saved else "orange"
                ),
                ft.Container(height=15),
                
                # QR Code Section
                ft.Text("Scan QR Code:", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                ft.Container(
                    content=ft.Image(src=qr_image_path, width=200, height=200, fit=ft.ImageFit.CONTAIN),
                    alignment=ft.alignment.center,
                    bgcolor="white",
                    border_radius=10,
                    padding=10
                ),
                ft.Text("Scan with your phone camera to add to Google Wallet", size=10, color="grey", text_align=ft.TextAlign.CENTER),
                
                ft.Container(height=15),
                
                # Link Section
                ft.Text("Or use link:", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.TextField(value=save_link, read_only=True, expand=True, text_size=10),
                    ft.IconButton(icon="content_copy", tooltip="Copy link", on_click=lambda e: page.set_clipboard(save_link))
                ]),
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Open in Google Wallet",
                    icon="open_in_new",
                    on_click=lambda e: page.launch_url(save_link),
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                ft.Container(height=10),
                ft.Text(f"Object ID: {object_id}", size=10, color="grey"),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            status_ref.current.value = "✅ Pass generated and saved to Google Wallet!"
            status_ref.current.color = "green"
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            status_ref.current.value = f"❌ Error: {str(ex)}"
            status_ref.current.color = "red"
            result_container_ref.current.content = None
        
        page.update()
    
    # Build UI
    ui = ft.Row([
        # Left Panel: Form
        ft.Container(
            width=500,
            content=ft.Column([
                ft.Text("Pass Generator", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Create individual passes for end users", size=12, color="grey"),
                ft.Divider(),
                
                ft.Container(height=10),
                
                ft.Text("Select Template", size=16, weight=ft.FontWeight.BOLD),
                ft.Dropdown(
                    ref=template_dropdown_ref,
                    label="Template Class",
                    hint_text="Choose a template",
                    width=400,
                    on_change=on_template_selected
                ),
                
                ft.Container(height=10),
                
                ft.Text("Pass Holder Information", size=16, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    ref=holder_name_ref,
                    label="Name *",
                    hint_text="e.g., John Doe",
                    width=400,
                    on_change=lambda e: update_preview()
                ),
                ft.TextField(
                    ref=holder_email_ref,
                    label="Email *",
                    hint_text="e.g., john@example.com",
                    width=400
                ),
                
                ft.Container(height=10),
                
                ft.Text("Pass Details", size=16, weight=ft.FontWeight.BOLD),
                dynamic_fields_container,
                
                ft.Container(height=20),
                
                ft.ElevatedButton(
                    "Generate Pass",
                    icon="add_card",
                    on_click=generate_pass,
                    width=400,
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                
                ft.Container(height=10),
                
                ft.Text(ref=status_ref, value="", size=12),
                
                ft.Container(height=10),
                
                ft.Container(ref=result_container_ref, content=None)
                
            ], spacing=10, scroll="auto"),
            padding=20
        ),
        
        # Right Panel: Preview
        ft.Container(
            expand=True,
            content=ft.Column([
                ft.Text("Live Preview", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("See how the pass will look", size=12, color="grey"),
                ft.Container(height=20),
                preview_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
            padding=20,
            bgcolor="grey100"
        )
    ], expand=True, spacing=0)
    
    # Load templates after UI is created
    load_templates()
    
    return ui
