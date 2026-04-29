"""
Apple Template Builder View
Allows users to create custom Apple Wallet (.pkpass) template blueprints.
Visually aligned to the Google Wallet builder for total workflow harmony.
"""

import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR
import configs
import uuid
from database.models import SessionLocal, ApplePassesTemplate

def create_apple_template_builder(page: ft.Page, state, api_client=None):
    """
    Create the redesigned Apple Template Builder interface.
    """
    
    # UI References
    template_name_tf = ft.TextField(
        label="Template Name *",
        hint_text="e.g., Coffee Rewards Template",
        width=380, border_radius=8, text_size=13
    )
    
    pass_style_dd = ft.Dropdown(
        label="Pass Style",
        value="generic",
        width=380, border_radius=8, text_size=13,
        options=[
            ft.dropdown.Option("generic", "Generic"),
            ft.dropdown.Option("storecard", "Store Card"),
            ft.dropdown.Option("boardingpass", "Boarding Pass"),
            ft.dropdown.Option("coupon", "Coupon"),
            ft.dropdown.Option("eventticket", "Event Ticket"),
        ]
    )
    
    status_text = ft.Text("", size=12)

    def on_save_click(e):
        tname = template_name_tf.value.strip()
        pstyle = pass_style_dd.value

        if not tname:
            status_text.value = "⚠️ Please provide a Template Name."
            status_text.color = "orange"
            page.update()
            return

        status_text.value = "⏳ Saving template..."
        status_text.color = "blue"
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
            def dialog_dismissed(evt):
                on_reset_click(None)

            def close_dlg(evt):
                page.close(succ_dlg)

            succ_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Success", weight=ft.FontWeight.BOLD),
                content=ft.Text(f"Apple Pass template blueprint '{tname}' successfully deployed.", size=13),
                on_dismiss=dialog_dismissed,
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(succ_dlg)
            
            # Refresh other views
            if state:
                state.refresh_ui("apple_templates_list")
                state.refresh_ui("apple_manage_templates_list")
        except Exception as ex:
            status_text.value = f"❌ Error: {str(ex)}"
            status_text.color = "red"
        
        page.update()

    def on_reset_click(e):
        template_name_tf.value = ""
        pass_style_dd.value = "generic"
        status_text.value = ""
        page.update()

    # Layout
    view_content = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR,
        content=ft.Column([
            ft.Text("Create New Template (Apple Wallet)", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Fill out core parameters to begin crafting your digital wallet blueprint.", color=TEXT_SECONDARY, size=13),
            ft.Container(height=8),
            
            card(ft.Column([
                section_title("Template Configuration", ft.Icons.STYLE),
                template_name_tf,
                pass_style_dd,
                
                ft.Container(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        "Save Blueprint",
                        icon=ft.Icons.SAVE,
                        on_click=on_save_click,
                        bgcolor=PRIMARY, color="white", height=45, width=200,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.OutlinedButton(
                        "Reset", 
                        icon=ft.Icons.REFRESH, 
                        on_click=on_reset_click,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], spacing=12),
                status_text,
            ], spacing=15)),
            
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    )

    return ft.Container(
        content=view_content,
        expand=True,
        bgcolor="white"
    )
