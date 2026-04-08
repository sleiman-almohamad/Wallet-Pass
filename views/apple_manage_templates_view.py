"""
Apple Manage Templates View
Allows users to list, update, and delete Apple Wallet templates.
"""

import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR, BORDER_COLOR
import configs

def build_apple_manage_templates_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Apple Manage Templates view.
    """
    
    # UI References
    templates_list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("", size=12)

    def load_templates():
        templates_list_column.controls.clear()
        status_text.value = "⏳ Loading templates..."
        status_text.color = "blue"
        page.update()

        try:
            templates = api_client.get_apple_templates() if api_client else []
            if not templates:
                templates_list_column.controls.append(
                    ft.Text("No Apple templates found. Create one in the Template Builder.", 
                            color=TEXT_SECONDARY, size=13, italic=True)
                )
                status_text.value = ""
            else:
                for t in templates:
                    templates_list_column.controls.append(
                        create_template_card(t)
                    )
                status_text.value = f"✅ Loaded {len(templates)} templates."
                status_text.color = "green"
        except Exception as e:
            status_text.value = f"❌ Error: {str(e)}"
            status_text.color = "red"
        
        page.update()

    def delete_template(template_id):
        try:
            api_client.delete_apple_template(template_id)
            
            # --- Success Dialog ---
            def close_dlg(e):
                page.close(del_dlg)

            del_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Template Deleted", weight=ft.FontWeight.BOLD),
                content=ft.Text(f"Template {template_id} has been permanently deleted.", size=13),
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(del_dlg)
            
            load_templates()
        except Exception as e:
            status_text.value = f"❌ Delete error: {str(e)}"
            status_text.color = "red"
            page.update()

    def create_template_card(t):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STYLE, color=PRIMARY, size=24),
                ft.Column([
                    ft.Text(t['template_name'], size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"ID: {t['template_id']} | Style: {t['pass_style']}", size=11, color=TEXT_SECONDARY),
                    ft.Text(f"Type: {t['pass_type_identifier']}", size=11, color=TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color="red700",
                    tooltip="Delete Template",
                    on_click=lambda _: delete_template(t['template_id'])
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=8,
            bgcolor="white"
        )

    # Register refresh callback
    if state:
        state.register_refresh_callback("apple_templates_list", load_templates)

    # Initial load
    load_templates()

    return ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=36, top=24, bottom=20),
        bgcolor=BG_COLOR,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Apple Templates", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                    ft.Text("List of all Apple Wallet pass templates stored in your database.", color=TEXT_SECONDARY, size=13),
                ], expand=True),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: load_templates(), tooltip="Refresh List")
            ]),
            ft.Container(height=10),
            status_text,
            ft.Container(
                content=templates_list_column,
                expand=True
            )
        ], spacing=10)
    )
