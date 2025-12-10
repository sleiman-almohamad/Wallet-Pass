"""
Template Builder Module - Simplified Version
Functional approach without UserControl for compatibility
"""

import flet as ft
from ui.models.template_state import TemplateState


def create_template_builder(page, api_client=None):
    """
    Create the template builder interface
    Returns a Container with the complete template builder UI
    """
    
    # Initialize state
    template_state = TemplateState()
    
    # Create all UI elements as refs so we can update them
    class_id_input_ref = ft.Ref[ft.TextField]()
    class_type_dropdown_ref = ft.Ref[ft.Dropdown]()
    issuer_input_ref = ft.Ref[ft.TextField]()
    header_input_ref = ft.Ref[ft.TextField]()
    card_title_input_ref = ft.Ref[ft.TextField]()
    save_status_ref = ft.Ref[ft.Text]()
    preview_container_ref = ft.Ref[ft.Container]()
    color_picker_container_ref = ft.Ref[ft.Container]()
    
    # Subscribe to state changes to update preview
    def on_state_change(data):
        if preview_container_ref.current:
            preview_container_ref.current.content = build_live_preview(data)
            page.update()
    
    template_state.subscribe(on_state_change)
    
    # Build live preview
    def build_live_preview(data):
        """Build the pass preview"""
        header = data.get("header", "Business Name")
        card_title = data.get("card_title", "Pass Title")
        bg_color = data.get("background_color", "#4285f4")
        logo_url = data.get("logo_url")
        hero_url = data.get("hero_url")
        fields = data.get("fields", [])
        
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
        
        # Hero image
        if hero_url:
            hero_control = ft.Container(
                height=150,
                content=ft.Image(src=hero_url, width=350, height=150, fit=ft.ImageFit.COVER)
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
        
        # Fields display
        if fields:
            field_widgets = [
                ft.Text(f"{field.get('label', 'Field')}: Sample", size=12, 
                       color="black" if i == 0 else "grey")
                for i, field in enumerate(fields[:3])
            ]
            fields_control = ft.Column(field_widgets, spacing=3)
        else:
            fields_control = ft.Column([
                ft.Text("John Doe", weight=ft.FontWeight.BOLD, size=14, color="black"),
                ft.Text("ID: 1234567890", size=12, color="grey")
            ])
        
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
                        ft.Text(header, color="white", weight=ft.FontWeight.BOLD, size=16, expand=True)
                    ])
                ),
                # Card Title
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(card_title, color="white", size=22, weight=ft.FontWeight.BOLD)
                ),
                # Hero Image
                hero_control,
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
                            fields_control
                        ])
                    ])
                )
            ], spacing=0)
        )
    
    # Save template function
    def save_template(e):
        data = template_state.get_all()
        
        if not data.get("class_id"):
            save_status_ref.current.value = "❌ Class ID is required"
            save_status_ref.current.color = "red"
            page.update()
            return
        
        save_status_ref.current.value = "⏳ Saving template..."
        save_status_ref.current.color = "blue"
        page.update()
        
        try:
            if api_client:
                result = api_client.create_class(
                    class_id=data["class_id"],
                    class_type=data["class_type"],
                    base_color=data["background_color"],
                    logo_url=data.get("logo_url", "")
                )
                save_status_ref.current.value = "✅ Template saved successfully!"
                save_status_ref.current.color = "green"
            else:
                save_status_ref.current.value = "⚠️ API client not connected"
                save_status_ref.current.color = "orange"
        except Exception as ex:
            save_status_ref.current.value = f"❌ Error: {str(ex)}"
            save_status_ref.current.color = "red"
        
        page.update()
    
    # Reset form function
    def reset_form(e):
        template_state.reset()
        class_id_input_ref.current.value = ""
        class_type_dropdown_ref.current.value = "Generic"
        issuer_input_ref.current.value = "Your Business"
        header_input_ref.current.value = "Business Name"
        card_title_input_ref.current.value = "Pass Title"
        save_status_ref.current.value = ""
        page.update()
    
    # Build the complete UI
    return ft.Row([
        # Left Panel: Editor
        ft.Container(
            width=550,
            content=ft.Column([
                ft.Text("Template Builder", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Create and customize your Google Wallet pass template", size=12, color="grey"),
                ft.Divider(),
                
                ft.Text("Basic Information", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    ref=class_id_input_ref,
                    label="Class ID *",
                    hint_text="e.g., SeasonTicket2025",
                    width=400,
                    on_change=lambda e: template_state.update("class_id", e.control.value)
                ),
                ft.Dropdown(
                    ref=class_type_dropdown_ref,
                    label="Class Type *",
                    value="Generic",
                    width=400,
                    options=[ft.dropdown.Option(ct) for ct in ["Generic", "EventTicket", "LoyaltyCard", "GiftCard", "TransitPass"]],
                    on_change=lambda e: template_state.update("class_type", e.control.value)
                ),
                ft.TextField(
                    ref=issuer_input_ref,
                    label="Issuer Name",
                    value="Your Business",
                    width=400,
                    on_change=lambda e: template_state.update("issuer_name", e.control.value)
                ),
                
                ft.Divider(height=20),
                
                ft.Text("Pass Content", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    ref=header_input_ref,
                    label="Header Text *",
                    value="Business Name",
                    width=400,
                    on_change=lambda e: template_state.update("header", e.control.value)
                ),
                ft.TextField(
                    ref=card_title_input_ref,
                    label="Card Title *",
                    value="Pass Title",
                    width=400,
                    on_change=lambda e: template_state.update("card_title", e.control.value)
                ),
                
                ft.Divider(height=20),
                
                ft.Text("Visual Customization", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Background Color", size=14, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="Hex Color",
                    value="#4285f4",
                    width=200,
                    prefix_text="#",
                    on_change=lambda e: template_state.update("background_color", f"#{e.control.value}") if len(e.control.value) == 6 else None
                ),
                
                ft.Divider(height=20),
                
                ft.Row([
                    ft.ElevatedButton("Save Template", icon="save", on_click=save_template),
                    ft.OutlinedButton("Reset", icon="refresh", on_click=reset_form)
                ], spacing=10),
                
                ft.Text(ref=save_status_ref, value="", size=12),
                
                ft.Container(height=50)
            ], scroll="auto", spacing=10),
            padding=20,
            bgcolor="white"
        ),
        
        # Right Panel: Live Preview
        ft.Container(
            expand=True,
            content=ft.Column([
                ft.Text("Live Preview", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("See how your pass will look in Google Wallet", size=12, color="grey"),
                ft.Container(height=20),
                ft.Container(
                    ref=preview_container_ref,
                    content=build_live_preview(template_state.get_all())
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
            bgcolor="grey100",
            padding=20
        )
    ], expand=True, spacing=0)
