import flet as ft
import json
from wallet_service import WalletClient
from api_client import APIClient
from field_schemas import get_fields_for_class_type
from google_wallet_parser import parse_google_wallet_class
from qr_generator import generate_qr_code
import configs
from ui.class_builder import create_template_builder
from ui.pass_generator import create_pass_generator


def main(page: ft.Page):
    page.title = "Google Wallet Verifier & Preview"
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.assets_dir = "assets"

    # --- Initialize Connection ---
    client = None
    try:
        client = WalletClient()
        # FIX: Changed ft.colors.GREEN to "green"
        connection_status = ft.Text("✅ Service Connected", color="green", size=12)
    except Exception as e:
        client = None
        # FIX: Changed ft.colors.RED to "red"
        connection_status = ft.Text(f"❌ Service Error: {e}", color="red", size=12)
    
    # --- Initialize API Client ---
    api_client = APIClient()
    
    # Check API health
    try:
        health = api_client.check_health()
        if health.get("status") == "healthy":
            api_status = ft.Text("✅ API Connected", color="green", size=12)
        else:
            api_status = ft.Text(f"⚠️ API: {health.get('database', 'unknown')}", color="orange", size=12)
    except Exception as e:
        api_status = ft.Text(f"❌ API Error: {e}", color="red", size=12)

    # --- Helper: Extract Visual Assets ---
    def parse_class_visuals(class_data):
        """
        Extracts colors, images, and texts from the JSON to build a visual preview.
        """
        visuals = {
            "bg_color": class_data.get("hexBackgroundColor", "#4285f4"), # Default Google Blue
            "logo_url": None,
            "hero_url": None,
            "title": "Google Wallet Pass",
            "issuer": "Issuer Name"
        }

        # 1. Extract Logo
        if "logo" in class_data and "sourceUri" in class_data["logo"]:
            visuals["logo_url"] = class_data["logo"]["sourceUri"].get("uri")
        
        # 2. Extract Hero Image (Banner)
        if "heroImage" in class_data and "sourceUri" in class_data["heroImage"]:
            visuals["hero_url"] = class_data["heroImage"]["sourceUri"].get("uri")
        
        # 3. Extract Issuer Name
        if "localizedIssuerName" in class_data:
            visuals["issuer"] = class_data["localizedIssuerName"].get("defaultValue", {}).get("value", "Issuer")
        elif "issuerName" in class_data:
            visuals["issuer"] = class_data["issuerName"]

        # 4. Extract Title (Varies by Class Type)
        if "eventName" in class_data: # Event Ticket
            visuals["title"] = class_data["eventName"].get("defaultValue", {}).get("value")
        elif "programName" in class_data: # Loyalty
            visuals["title"] = class_data["programName"].get("defaultValue", {}).get("value")
        elif "localizedShortTitle" in class_data: # Generic
            visuals["title"] = class_data["localizedShortTitle"].get("defaultValue", {}).get("value")
        
        return visuals

    # --- UI Component: Simulated Card ---
    def build_preview_card(visuals):
        """
        Constructs a UI Container that looks like a mobile wallet pass.
        """
        # Prepare Logo Control
        logo_control = ft.Container()
        if visuals["logo_url"]:
            logo_control = ft.Image(src=visuals["logo_url"], width=50, height=50, fit=ft.ImageFit.CONTAIN, border_radius=25)
        
        # Prepare Hero Image Control
        # FIX: Changed ft.colors.BLACK12 to "black12"
        hero_control = ft.Container(height=150, bgcolor="black12", alignment=ft.alignment.center, content=ft.Text("No Hero Image", size=10))
        if visuals["hero_url"]:
            hero_control = ft.Image(src=visuals["hero_url"], width=300, height=150, fit=ft.ImageFit.COVER)

        # Build the Card Container
        return ft.Container(
            width=320, # Approximate mobile width
            bgcolor=visuals["bg_color"],
            border_radius=15,
            padding=0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE, # Clip overflow images
            # FIX: Changed ft.colors.BLACK26 to "black26"
            shadow=ft.BoxShadow(blur_radius=10, color="black26"),
            content=ft.Column([
                # Top Section: Logo & Issuer Name
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        logo_control,
                        ft.Text(visuals["issuer"], color="white", weight="bold", size=14, expand=True)
                    ], alignment=ft.MainAxisAlignment.START)
                ),
                # Middle Section: Title
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(visuals["title"], color="white", size=20, weight="bold")
                ),
                # Image Section
                hero_control,
                # Bottom Mockup Section (QR & Details)
                ft.Container(
                    height=120,
                    bgcolor="white",
                    padding=15,
                    width=320,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=10),
                        ft.Row([
                            ft.Icon(name="qr_code_2", size=50, color="black"),
                            ft.Column([
                                ft.Text("John Doe", weight="bold", size=14, color="black"),
                                ft.Text("1234 5678 9000", size=12, color="grey")
                            ])
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ])
                )
            ], spacing=0)
        )

    # --- Main UI Elements ---
    search_type = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="class", label="Template (Class)"),
            ft.Radio(value="object", label="User Pass (Object)")
        ]),
        value="class"
    )

    id_input = ft.TextField(
        label="ID (Suffix Only or Full ID)", 
        hint_text="e.g. Hannover96_SeasonTicket_2025_v1",
        expand=True,
        autofocus=True
    )

    # Initialize Template Builder
    template_builder = create_template_builder(page, api_client=api_client)
    
    # Create Manage Templates tab content
    manage_templates_dropdown = ft.Dropdown(
        label="Select Template Class",
        hint_text="Choose a class to manage",
        width=400,
        options=[]
    )
    
    manage_status = ft.Text("", size=12)
    
    # Form fields for editing template
    edit_class_id_field = ft.TextField(
        label="Class ID",
        width=400,
        read_only=True,
        bgcolor="grey100"
    )
    
    edit_class_type_field = ft.TextField(
        label="Class Type",
        width=400,
        read_only=True,
        bgcolor="grey100"
    )
    
    edit_issuer_name_field = ft.TextField(
        label="Issuer Name",
        hint_text="e.g., Your Business Name",
        width=400
    )
    
    edit_header_text_field = ft.TextField(
        label="Header Text",
        hint_text="e.g., Business Name",
        width=400
    )
    
    edit_card_title_field = ft.TextField(
        label="Card Title",
        hint_text="e.g., Event Ticket",
        width=400
    )
    
    edit_background_color_field = ft.TextField(
        label="Background Color (Hex)",
        hint_text="e.g., #4285f4",
        width=400,
        prefix_text="#"
    )
    
    edit_logo_url_field = ft.TextField(
        label="Logo URL",
        hint_text="e.g., https://example.com/logo.png",
        width=400
    )
    
    # Preview container
    preview_container = ft.Container(
        content=ft.Text("Select a template and click 'Show' to preview", color="grey"),
        alignment=ft.alignment.center
    )
    
    def build_preview(class_data):
        """Build visual pass preview from class data"""
        bg_color = class_data.get("base_color", "#4285f4")
        logo_url = class_data.get("logo_url")
        header_text = class_data.get("header_text", "Business Name")
        card_title = class_data.get("card_title", "Pass Title")
        
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
                        ft.Icon("image", size=40, color="grey"),
                        ft.Text("Hero Image", size=12, color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                # Bottom: QR & Details
                ft.Container(
                    bgcolor="white",
                    padding=15,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=12),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Container(
                                width=80, height=80, bgcolor="grey200", border_radius=5,
                                content=ft.Icon("qr_code_2", size=60, color="grey"),
                                alignment=ft.alignment.center
                            ),
                            ft.Container(width=15),
                            ft.Column([
                                ft.Text("John Doe", weight=ft.FontWeight.BOLD, size=14, color="black"),
                                ft.Text("ID: 1234567890", size=12, color="grey")
                            ])
                        ])
                    ])
                )
            ], spacing=0)
        )
    
    def update_preview():
        """Update preview based on current field values"""
        if not edit_class_id_field.value:
            return
        
        class_data = {
            "base_color": f"#{edit_background_color_field.value}" if edit_background_color_field.value and not edit_background_color_field.value.startswith("#") else edit_background_color_field.value or "#4285f4",
            "logo_url": edit_logo_url_field.value,
            "header_text": edit_header_text_field.value or "Business Name",
            "card_title": edit_card_title_field.value or "Pass Title"
        }
        
        preview_container.content = build_preview(class_data)
        page.update()
    
    # Add on_change handlers to update preview
    edit_header_text_field.on_change = lambda e: update_preview()
    edit_card_title_field.on_change = lambda e: update_preview()
    edit_background_color_field.on_change = lambda e: update_preview()
    edit_logo_url_field.on_change = lambda e: update_preview()
    
    def load_template_classes():
        """Load classes from database into dropdown"""
        try:
            classes = api_client.get_classes()
            if classes and len(classes) > 0:
                manage_templates_dropdown.options = [
                    ft.dropdown.Option(cls["class_id"]) 
                    for cls in classes
                ]
                manage_templates_dropdown.value = classes[0]["class_id"]
                manage_status.value = f"✅ Loaded {len(classes)} template(s)"
                manage_status.color = "green"
            else:
                manage_templates_dropdown.options = []
                manage_templates_dropdown.value = None
                manage_status.value = "ℹ️ No templates found. Create one in Template Builder tab."
                manage_status.color = "blue"
            page.update()
        except Exception as e:
            manage_status.value = f"❌ Error loading classes: {e}"
            manage_status.color = "red"
            page.update()
    
    def show_template(e):
        """Fetch and display template for editing"""
        if not manage_templates_dropdown.value:
            manage_status.value = "❌ Please select a class"
            manage_status.color = "red"
            page.update()
            return
        
        manage_status.value = "⏳ Loading template..."
        manage_status.color = "blue"
        page.update()
        
        try:
            class_id = manage_templates_dropdown.value
            
            # Get class details from database
            class_data = api_client.get_class(class_id)
            
            if not class_data:
                manage_status.value = f"❌ Class '{class_id}' not found in database"
                manage_status.color = "red"
                page.update()
                return
            
            # Populate form fields
            edit_class_id_field.value = class_data.get("class_id", "")
            edit_class_type_field.value = class_data.get("class_type", "Generic")
            
            # Handle issuer_name with proper default
            issuer_name = class_data.get("issuer_name")
            edit_issuer_name_field.value = issuer_name if issuer_name else "Your Business"
            
            edit_header_text_field.value = class_data.get("header_text", "")
            edit_card_title_field.value = class_data.get("card_title", "")
            
            # Handle color with or without #
            color = class_data.get("base_color", "")
            if color and color.startswith("#"):
                edit_background_color_field.value = color[1:]
            else:
                edit_background_color_field.value = color
            
            edit_logo_url_field.value = class_data.get("logo_url", "")
            
            # Update preview
            preview_container.content = build_preview(class_data)
            
            manage_status.value = f"✅ Template loaded. Edit fields and click 'Update' to save changes."
            manage_status.color = "green"
            
        except Exception as ex:
            manage_status.value = f"❌ Error: {str(ex)}"
            manage_status.color = "red"
        
        page.update()
    
    def update_template(e):
        """Save template changes to database"""
        if not edit_class_id_field.value:
            manage_status.value = "❌ No template loaded"
            manage_status.color = "red"
            page.update()
            return
        
        manage_status.value = "⏳ Updating template..."
        manage_status.color = "blue"
        page.update()
        
        try:
            class_id = edit_class_id_field.value
            
            # Prepare color value
            color = edit_background_color_field.value
            if color and not color.startswith("#"):
                color = f"#{color}"
            
            # Update via API
            result = api_client.update_class(
                class_id=class_id,
                base_color=color if color else None,
                logo_url=edit_logo_url_field.value if edit_logo_url_field.value else None,
                issuer_name=edit_issuer_name_field.value if edit_issuer_name_field.value else None,
                header_text=edit_header_text_field.value if edit_header_text_field.value else None,
                card_title=edit_card_title_field.value if edit_card_title_field.value else None
            )
            
            manage_status.value = f"✅ Template '{class_id}' updated successfully!"
            manage_status.color = "green"
            
            # Refresh preview
            update_preview()
            
        except Exception as ex:
            manage_status.value = f"❌ Error: {str(ex)}"
            manage_status.color = "red"
        
        page.update()
    
    def insert_to_google(e):
        """Insert selected class to Google Wallet"""
        if not edit_class_id_field.value:
            manage_status.value = "❌ Please load a template first"
            manage_status.color = "red"
            page.update()
            return
        
        manage_status.value = "⏳ Inserting to Google Wallet..."
        manage_status.color = "blue"
        page.update()
        
        try:
            class_id = edit_class_id_field.value
            class_type = edit_class_type_field.value
            
            # Ensure class_id has issuer prefix
            full_class_id = class_id if class_id.startswith(configs.ISSUER_ID) else f"{configs.ISSUER_ID}.{class_id}"
            
            # Prepare color
            color = edit_background_color_field.value
            if color and not color.startswith("#"):
                color = f"#{color}"
            
            # Build class data for Google Wallet API
            google_class_data = {
                "id": full_class_id,
                "issuerName": edit_issuer_name_field.value or "Your Business",
                "reviewStatus": "UNDER_REVIEW",
            }
            
            # Add background color if available
            if color:
                google_class_data["hexBackgroundColor"] = color
            
            # Add logo if available
            if edit_logo_url_field.value:
                google_class_data["logo"] = {
                    "sourceUri": {
                        "uri": edit_logo_url_field.value
                    }
                }
            
            # Add type-specific fields
            if class_type == "Generic":
                # Use header_text from database, fallback to issuer_name
                header_value = edit_header_text_field.value or edit_issuer_name_field.value or "Business Name"
                card_title_value = edit_card_title_field.value or "Pass Title"
                
                google_class_data["header"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": header_value
                    }
                }
                google_class_data["cardTitle"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": card_title_value
                    }
                }
            elif class_type == "EventTicket":
                event_name = edit_header_text_field.value or edit_issuer_name_field.value or "Event Name"
                google_class_data["eventName"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": event_name
                    }
                }
            elif class_type == "LoyaltyCard":
                program_name = edit_header_text_field.value or edit_issuer_name_field.value or "Loyalty Program"
                google_class_data["programName"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": program_name
                    }
                }
            
            # Insert to Google Wallet using WalletClient
            if client:
                result = client.create_pass_class(google_class_data, class_type)
                manage_status.value = f"✅ Class '{class_id}' successfully inserted to Google Wallet!"
                manage_status.color = "green"
            else:
                manage_status.value = "❌ Google Wallet service not connected"
                manage_status.color = "red"
                
        except Exception as ex:
            manage_status.value = f"❌ Error: {str(ex)}"
            manage_status.color = "red"
        
        page.update()
    
    # Load classes on startup
    load_template_classes()
    
    manage_templates_content = ft.Container(
        content=ft.Row([
            # Left Panel: Controls and Edit Fields
            ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text("Manage Templates", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Select, preview, and edit your pass templates", size=12, color="grey"),
                    ft.Divider(),
                    
                    ft.Container(height=10),
                    
                    manage_templates_dropdown,
                    
                    ft.Container(height=10),
                    
                    ft.Row([
                        ft.ElevatedButton(
                            "Show",
                            icon="visibility",
                            on_click=show_template,
                            style=ft.ButtonStyle(
                                bgcolor="green",
                                color="white"
                            )
                        ),
                        ft.OutlinedButton(
                            "Refresh List",
                            icon="refresh",
                            on_click=lambda e: load_template_classes()
                        )
                    ], spacing=10),
                    
                    ft.Divider(height=20),
                    
                    ft.Text("Template Details", size=16, weight=ft.FontWeight.BOLD),
                    
                    edit_class_id_field,
                    edit_class_type_field,
                    edit_issuer_name_field,
                    edit_header_text_field,
                    edit_card_title_field,
                    edit_background_color_field,
                    edit_logo_url_field,
                    
                    ft.Divider(height=20),
                    
                    ft.ElevatedButton(
                        "Update Template",
                        icon="save",
                        on_click=update_template,
                        width=400,
                        style=ft.ButtonStyle(
                            bgcolor="orange",
                            color="white"
                        )
                    ),
                    
                    ft.Container(height=10),
                    
                    ft.ElevatedButton(
                        "Insert to Google Wallet",
                        icon="cloud_upload",
                        on_click=insert_to_google,
                        width=400,
                        style=ft.ButtonStyle(
                            bgcolor="blue",
                            color="white"
                        )
                    ),
                    
                    ft.Container(height=10),
                    
                    manage_status
                    
                ], spacing=10, scroll="auto"),
                padding=20
            ),
            
            # Right Panel: Live Preview
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text("Live Preview", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("See how your pass will look in Google Wallet", size=12, color="grey"),
                    ft.Container(height=20),
                    preview_container
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                padding=20,
                bgcolor="grey100"
            )
        ], expand=True, spacing=0),
        expand=True
    )
    
    # Create Pass Generator tab
    pass_generator = create_pass_generator(page, api_client=api_client, wallet_client=client)
    
    # Tabs for switching views
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Template Builder 🎨", content=template_builder),
            ft.Tab(text="Pass Generator 🎫", content=pass_generator),
            ft.Tab(text="Manage Templates 📋", content=manage_templates_content),
        ],
        expand=True
    )

    # --- Google Wallet Import Section ---
    google_class_id_input = ft.TextField(
        label="Google Wallet Class ID",
        hint_text="e.g., 3388000000023033675.SeasonTicket2025",
        width=400,
        expand=True
    )
    
    import_status = ft.Text("", size=12)
    
    def fetch_from_google_wallet(e):
        """Fetch class from Google Wallet and save to database"""
        class_id = google_class_id_input.value.strip()
        
        if not class_id:
            import_status.value = "❌ Please enter a Class ID"
            import_status.color = "red"
            page.update()
            return
        
        import_status.value = "⏳ Fetching from Google Wallet..."
        import_status.color = "blue"
        page.update()
        
        try:
            # Fetch from Google Wallet using existing WalletClient
            if not client:
                raise Exception("Google Wallet service not connected")
            
            google_class = client.get_class(class_id)
            
            # Parse the Google Wallet class
            metadata = parse_google_wallet_class(google_class)
            
            # Save to local database via API
            result = api_client.create_class(
                class_id=metadata['class_id'],
                class_type=metadata['class_type'],
                base_color=metadata['base_color'],
                logo_url=metadata['logo_url']
            )
            
            import_status.value = f"✅ Imported: {metadata['class_id']} ({metadata['class_type']})"
            import_status.color = "green"
            
            # Refresh class list and select the new class
            load_classes()
            class_dropdown.value = metadata['class_id']
            
            # Trigger field generation
            on_class_change(None)
            
            # Clear input
            google_class_id_input.value = ""
            
        except Exception as ex:
            import_status.value = f"❌ {str(ex)}"
            import_status.color = "red"
        
        page.update()
    
    fetch_google_btn = ft.ElevatedButton(
        "Fetch from Google Wallet",
        icon="cloud_download",
        on_click=fetch_from_google_wallet
    )

    # --- Create Pass Form Fields ---
    class_dropdown = ft.Dropdown(
        label="Select Class",
        hint_text="Choose a pass class",
        width=400,
        options=[],
        on_change=lambda e: on_class_change(e)
    )
    
    object_id_field = ft.TextField(
        label="Object ID",
        hint_text="e.g., PASS_001",
        width=400
    )
    
    holder_name_field = ft.TextField(
        label="Holder Name",
        hint_text="e.g., John Doe",
        width=400
    )
    
    holder_email_field = ft.TextField(
        label="Holder Email",
        hint_text="e.g., john.doe@example.com",
        width=400,
        keyboard_type=ft.KeyboardType.EMAIL
    )
    
    status_dropdown = ft.Dropdown(
        label="Status",
        value="Active",
        width=400,
        options=[
            ft.dropdown.Option("Active"),
            ft.dropdown.Option("Expired")
        ]
    )
    
    # Container for dynamic pass data fields
    dynamic_fields_container = ft.Column([], spacing=10)
    dynamic_field_refs = {}  # Store references to dynamic fields
    
    create_result = ft.Text("", size=14)
    
    def generate_dynamic_fields(class_type: str):
        """Generate form fields based on class type"""
        # Clear previous fields
        dynamic_fields_container.controls.clear()
        dynamic_field_refs.clear()
        
        # Get field schema for this class type
        fields_schema = get_fields_for_class_type(class_type)
        
        # Add header
        dynamic_fields_container.controls.append(
            ft.Text("Pass Details", size=16, weight="bold", color="blue")
        )
        
        # Generate fields based on schema
        for field_def in fields_schema:
            field_name = field_def["name"]
            field_label = field_def["label"]
            field_type = field_def["type"]
            field_hint = field_def.get("hint", "")
            
            # Create appropriate field based on type
            if field_type == "number":
                field = ft.TextField(
                    label=field_label,
                    hint_text=field_hint,
                    width=400,
                    keyboard_type=ft.KeyboardType.NUMBER
                )
            elif field_type in ["date", "datetime"]:
                field = ft.TextField(
                    label=field_label,
                    hint_text=field_hint,
                    width=400,
                    keyboard_type=ft.KeyboardType.DATETIME
                )
            else:  # text
                field = ft.TextField(
                    label=field_label,
                    hint_text=field_hint,
                    width=400
                )
            
            # Store reference to field
            dynamic_field_refs[field_name] = field
            dynamic_fields_container.controls.append(field)
        
        page.update()
    
    def on_class_change(e):
        """Handle class selection change"""
        if not class_dropdown.value:
            return
        
        try:
            # Fetch class details
            class_data = api_client.get_class(class_dropdown.value)
            if class_data:
                class_type = class_data.get("class_type", "Generic")
                generate_dynamic_fields(class_type)
        except Exception as ex:
            create_result.value = f"❌ Error loading class: {ex}"
            create_result.color = "red"
            page.update()
    
    def load_classes():
        """Load available classes from API"""
        try:
            classes = api_client.get_classes()
            class_dropdown.options = [
                ft.dropdown.Option(cls["class_id"]) 
                for cls in classes
            ]
            if classes:
                class_dropdown.value = classes[0]["class_id"]
            page.update()
        except Exception as e:
            create_result.value = f"❌ Error loading classes: {e}"
            create_result.color = "red"
            page.update()
    
    def submit_pass(e):
        """Submit new pass to API"""
        # Validate required fields
        if not all([class_dropdown.value, object_id_field.value, 
                   holder_name_field.value, holder_email_field.value]):
            create_result.value = "❌ Please fill in all required fields"
            create_result.color = "red"
            page.update()
            return
        
        # Collect data from dynamic fields
        pass_data = {}
        for field_name, field_ref in dynamic_field_refs.items():
            if field_ref.value and field_ref.value.strip():
                # Try to convert numbers
                value = field_ref.value.strip()
                try:
                    # Check if it's a number
                    if value.replace('.', '', 1).isdigit():
                        pass_data[field_name] = float(value) if '.' in value else int(value)
                    else:
                        pass_data[field_name] = value
                except:
                    pass_data[field_name] = value
        
        # Submit to API (database)
        try:
            create_result.value = "⏳ Creating pass..."
            create_result.color = "blue"
            page.update()
            
            # Ensure object ID has Issuer ID prefix
            object_id = object_id_field.value.strip()
            if not object_id.startswith(configs.ISSUER_ID):
                object_id = f"{configs.ISSUER_ID}.{object_id}"
            
            # Save to database
            result = api_client.create_pass(
                object_id=object_id,
                class_id=class_dropdown.value,
                holder_name=holder_name_field.value.strip(),
                holder_email=holder_email_field.value.strip(),
                status=status_dropdown.value,
                pass_data=pass_data
            )
            
            # Get class details to determine type
            class_data = api_client.get_class(class_dropdown.value)
            class_type = class_data.get("class_type", "Generic") if class_data else "Generic"
            
            # Create pass object in Google Wallet
            if client:
                try:
                    create_result.value = "⏳ Pushing to Google Wallet..."
                    page.update()
                    
                    # Build pass object based on type
                    if class_type == "EventTicket":
                        pass_obj = client.build_event_ticket_object(
                            object_id=object_id,
                            class_id=class_dropdown.value,
                            holder_name=holder_name_field.value.strip(),
                            holder_email=holder_email_field.value.strip(),
                            pass_data=pass_data
                        )
                    elif class_type == "LoyaltyCard":
                        pass_obj = client.build_loyalty_object(
                            object_id=object_id,
                            class_id=class_dropdown.value,
                            holder_name=holder_name_field.value.strip(),
                            holder_email=holder_email_field.value.strip(),
                            pass_data=pass_data
                        )
                    else:
                        pass_obj = client.build_generic_object(
                            object_id=object_id,
                            class_id=class_dropdown.value,
                            holder_name=holder_name_field.value.strip(),
                            holder_email=holder_email_field.value.strip(),
                            pass_data=pass_data
                        )
                    
                    # Create in Google Wallet
                    client.create_pass_object(pass_obj, class_type)
                    
                    # Generate Save to Wallet link
                    save_link = client.generate_save_link(object_id, class_type)
                    
                    # Generate QR code
                    qr_filename = f"qr_{object_id.replace('.', '_')}"
                    qr_path = generate_qr_code(save_link, qr_filename)
                    
                    create_result.value = f"✅ Pass created successfully!\n📱 Scan QR code below to add to your wallet"
                    create_result.color = "green"
                    
                    # Show QR code in a dialog
                    def close_dialog(e):
                        qr_dialog.open = False
                        page.update()
                    
                    qr_dialog = ft.AlertDialog(
                        title=ft.Text("Scan to Add to Google Wallet"),
                        content=ft.Column([
                            ft.Image(src=qr_path, width=300, height=300),
                            ft.Text("Scan this QR code with your phone", size=14, text_align="center"),
                            ft.Text(f"Pass ID: {object_id}", size=12, color="grey"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        actions=[
                            ft.TextButton("Close", on_click=close_dialog)
                        ],
                    )
                    
                    page.dialog = qr_dialog
                    qr_dialog.open = True
                    
                except Exception as wallet_ex:
                    create_result.value = f"✅ Pass saved to database\n⚠️ Google Wallet: {str(wallet_ex)}"
                    create_result.color = "orange"
            else:
                create_result.value = f"✅ {result.get('message', 'Pass created successfully!')}\n⚠️ Google Wallet service not connected"
                create_result.color = "orange"
            
            # Clear form
            object_id_field.value = ""
            holder_name_field.value = ""
            holder_email_field.value = ""
            status_dropdown.value = "Active"
            
            # Clear dynamic fields
            for field_ref in dynamic_field_refs.values():
                field_ref.value = ""
            
        except Exception as ex:
            create_result.value = f"❌ {str(ex)}"
            create_result.color = "red"
        
        page.update()
    
    submit_btn = ft.ElevatedButton(
        "Create Pass",
        icon="add_circle",
        on_click=submit_pass,
        width=400
    )
    
    
    # Build Create Pass Tab Content - DISABLED (tab removed)
    # The following code was for the old Create Pass tab that has been removed
    # Keeping it commented for reference
    """
    tabs.tabs[2].content = ft.Container(
        content=ft.Column([
            ft.Text("Create New Pass", size=20, weight="bold"),
            ft.Divider(),
            
            # Google Wallet Import Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Import from Google Wallet", size=16, weight="bold", color="purple"),
                    ft.Row([google_class_id_input, fetch_google_btn], alignment=ft.MainAxisAlignment.START),
                    import_status,
                ], spacing=10),
                bgcolor="purple12",
                padding=15,
                border_radius=10
            ),
            
            ft.Divider(height=20),
            ft.Text("OR", size=14, weight="bold", text_align="center"),
            ft.Divider(height=20),
            
            # Existing class selection
            ft.Text("Select Existing Class", size=16, weight="bold", color="blue"),
            ft.Row([class_dropdown, refresh_classes_btn], alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(),
            
            # Pass details
            ft.Text("Pass Information", size=16, weight="bold", color="blue"),
            object_id_field,
            holder_name_field,
            holder_email_field,
            status_dropdown,
            ft.Divider(),
            dynamic_fields_container,  # Dynamic fields based on class type
            ft.Divider(),
            submit_btn,
            ft.Divider(),
            create_result
        ], scroll="auto", spacing=15),
        padding=20
    )
    """
    
    # Load classes on startup - DISABLED (old Create Pass tab code)
    # load_classes()



    # OLD SEARCH FUNCTIONALITY - DISABLED (incompatible with new tab structure)
    # def run_search(e):
    #     if not client: return
    #     input_val = id_input.value.strip()

    # search_btn = ft.ElevatedButton("Search", icon="search", on_click=run_search)

    page.add(
        ft.Row([
            ft.Image(src="B2F.png", width=150, height=150)
        ],),
        ft.Row([connection_status, ft.Text(" | "), api_status]),
        # search_type,  # Removed old search UI
        # ft.Row([id_input, search_btn]),  # Removed old search UI
        ft.Divider(),
        tabs
    )

if __name__ == "__main__":
    ft.app(target=main)
