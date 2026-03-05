"""
Root View
Assembles the top-level header, status bar, and tab container.
"""

import flet as ft
from ui.class_builder import create_template_builder
from ui.pass_generator import create_pass_generator
from views.manage_templates_view import build_manage_templates_view
from views.manage_passes_view import build_manage_passes_view


def build_root_view(page: ft.Page, state) -> list:
    """
    Build every top-level control that gets added to ``page``.

    Returns a list of Flet controls: [header, status_bar, divider, tabs].
    """
    api_client = state.api_client
    wallet_client = state.wallet_client

    # ── Connection status indicators ──
    if state.wallet_connected:
        connection_status = ft.Text("✅ Service Connected", color="green", size=12)
    else:
        connection_status = ft.Text("❌ Service Not Connected", color="red", size=12)

    health = state.check_api_health()
    if state.api_connected:
        api_status = ft.Text("✅ API Connected", color="green", size=12)
    else:
        detail = health.get("database", health.get("detail", "unknown"))
        api_status = ft.Text(f"⚠️ API: {detail}", color="orange", size=12)

    # ── Tab contents ──
    template_builder = create_template_builder(page, api_client=api_client)
    pass_generator = create_pass_generator(page, api_client=api_client, wallet_client=wallet_client)
    manage_templates = build_manage_templates_view(page, state, api_client)
    manage_passes = build_manage_passes_view(page, state, api_client)

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Template Builder 🎨", content=template_builder),
            ft.Tab(text="Pass Generator 🎫", content=pass_generator),
            ft.Tab(text="Manage Templates 📋", content=manage_templates),
            ft.Tab(text="Manage Passes", icon="contact_page", content=manage_passes),
        ],
        expand=True,
    )

    # ── Assemble top-level controls ──
    return [
        ft.Row([ft.Image(src="B2F.png", width=150, height=150)]),
        ft.Row([connection_status, ft.Text(" | "), api_status]),
        ft.Divider(),
        tabs,
    ]
