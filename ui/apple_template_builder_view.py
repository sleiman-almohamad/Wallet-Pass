"""
Apple Template Builder View
Allows users to create and manage Apple Wallet (.pkpass) templates.
"""

import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR
import configs
import uuid
from database.models import SessionLocal, ApplePassesTemplate

def create_apple_template_builder(page: ft.Page, state, api_client=None):
    """
    Create the Apple Template Builder interface.
    """
    
    # UI References
    template_name_ref = ft.Ref[ft.TextField]()
    pass_style_ref = ft.Ref[ft.Dropdown]()
    status_text_ref = ft.Ref[ft.Text]()

    def on_save_click(e):
        tname = template_name_ref.current.value
        pstyle = pass_style_ref.current.value

        if not all([tname, pstyle]):
            status_text_ref.current.value = "⚠️ Please fill all required fields."
            status_text_ref.current.color = "orange"
            page.update()
            return

        status_text_ref.current.value = "⏳ Saving template..."
        status_text_ref.current.color = "blue"
        page.update()

        try:
            tid = str(uuid.uuid4())
            ptid = configs.APPLE_PASS_TYPE_ID
            teamid = configs.APPLE_TEAM_ID

            with SessionLocal() as db_session:
                template = ApplePassesTemplate(
                    template_id=tid,
                    template_name=tname,
                    pass_style=pstyle,
                    pass_type_identifier=ptid,
                    team_identifier=teamid
                )
                db_session.add(template)
                db_session.commit()
            
            # --- Success Dialog ---
            def dialog_dismissed(e):
                on_reset_click(None)
                page.update()

            def close_dlg(e):
                page.close(succ_dlg)

            succ_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Template Created", weight=ft.FontWeight.BOLD),
                content=ft.Text(f"Apple Pass template '{tname}' has been created successfully.", size=13),
                on_dismiss=dialog_dismissed,
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(succ_dlg)
            
            status_text_ref.current.value = ""
            
            # Clear form
            template_name_ref.current.value = ""
            pass_style_ref.current.value = "generic"
            
            # Refresh UI lists
            if state:
                state.refresh_ui("apple_templates_list")
        except Exception as ex:
            status_text_ref.current.value = f"❌ Error: {str(ex)}"
            status_text_ref.current.color = "red"
        
        page.update()

    def on_reset_click(e):
        template_name_ref.current.value = ""
        pass_style_ref.current.value = "generic"
        status_text_ref.current.value = ""
        page.update()

    # Layout
    view_content = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR,
        content=ft.Column([
            ft.Text("Apple Template Builder", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Configure your Apple Wallet pass templates and certificates.", color=TEXT_SECONDARY, size=13),
            ft.Container(height=10),
            
            card(ft.Column([
                section_title("Template Metadata", ft.Icons.SETTINGS_OUTLINED),
                ft.Text("Basic identifiers and branding name for this template.", size=12, color=TEXT_SECONDARY),
                ft.Row([
                    ft.TextField(
                        ref=template_name_ref,
                        label="Template Name *",
                        hint_text="e.g., My Store Loyalty",
                        expand=True, border_radius=8, text_size=13,
                    ),
                ], spacing=15),
                
                ft.Container(height=5),
                
                section_title("Apple Certificates & Style", ft.Icons.VERIFIED_OUTLINED),
                ft.Text("Style must match your Pass Type ID and Certificate capabilities. Technical identifiers are auto-fetched.", size=12, color=TEXT_SECONDARY),
                ft.Dropdown(
                    ref=pass_style_ref,
                    label="Pass Style *",
                    value="generic",
                    border_radius=8, text_size=13,
                    options=[
                        ft.dropdown.Option("generic", "Generic"),
                        ft.dropdown.Option("storeCard", "Store Card"),
                        ft.dropdown.Option("boardingPass", "Boarding Pass"),
                        ft.dropdown.Option("coupon", "Coupon"),
                        ft.dropdown.Option("eventTicket", "Event Ticket"),
                    ]
                ),
                
                ft.Container(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        "Save Apple Template",
                        icon=ft.Icons.SAVE_ALT_OUTLINED,
                        on_click=on_save_click,
                        bgcolor=PRIMARY, color="white", height=45,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.OutlinedButton(
                        "Reset Form", 
                        icon=ft.Icons.REFRESH, 
                        on_click=on_reset_click,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], spacing=12),
                ft.Text(ref=status_text_ref, value="", size=12),
            ], spacing=15)),
            
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    )

    return ft.Container(
        content=view_content,
        expand=True,
        bgcolor="white"
    )
