"""
Root View — Sidebar-Routed Shell
Replaces the old tab-based layout with a categorised sidebar + content area.
"""

import flet as ft
from ui.theme import BG_COLOR, PRIMARY, TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR, SIDEBAR_WIDTH
from ui.components.sidebar import build_sidebar, PREVIEW_VIEWS
from ui.components.mobile_mockup import MobileMockupPreview
from ui.class_builder import create_template_builder
from ui.apple_template_builder_view import create_apple_template_builder
from views.google_generator_view import build_google_generator_view
from views.apple_generator_view import build_apple_generator_view
from views.manage_templates_view import build_manage_templates_view
from views.apple_manage_templates_view import build_apple_manage_templates_view
from views.google_manage_passes_view import build_google_manage_passes_view
from views.apple_manage_passes_view import build_apple_manage_passes_view
from views.send_notification_view import build_send_notification_view
from views.campaign_management_view import build_campaign_management_view
from utils.db_backup_tool import DatabaseBackupTool


def build_root_view(page: ft.Page, state) -> list:
    """
    Build the sidebar-routed dashboard shell.
    Returns a list with a single Row that fills the page.
    """
    api_client = state.api_client
    wallet_client = state.wallet_client
    backup_tool = DatabaseBackupTool()

    # Shared preview instance (reused across generator / manage views)
    preview = MobileMockupPreview()
    preview_widget = preview.build()

    # ── Mutable state ──
    active_key = "g_template_builder"
    sidebar_container = ft.Container()
    content_container = ft.Container(expand=True)
    preview_container = ft.Container(width=0)  # hidden initially

    # ── View cache (lazily populated) ──
    view_cache: dict = {}

    # ── Build individual views ──
    def _get_view(key):
        if key in view_cache:
            return view_cache[key]

        if key == "g_template_builder":
            v = create_template_builder(page, state, api_client=api_client)
        elif key == "g_manage_templates":
            v = build_manage_templates_view(page, state, api_client)
        elif key == "g_pass_generator":
            v = build_google_generator_view(page, state, api_client, wallet_client, preview)
        elif key == "g_manage_passes":
            v = build_google_manage_passes_view(page, state, api_client, preview)
        elif key == "a_template_builder":
            v = create_apple_template_builder(page, state, api_client=api_client)
        elif key == "a_manage_templates":
            v = build_apple_manage_templates_view(page, state, api_client)
        elif key == "a_pass_generator":
            v = build_apple_generator_view(page, state, api_client, preview)
        elif key == "a_manage_passes":
            v = build_apple_manage_passes_view(page, state, api_client, preview)
        elif key == "notifications":
            v = build_send_notification_view(page, state, api_client)
        elif key == "qr_campaigns":
            v = build_campaign_management_view(page, state, api_client)
        elif key == "settings":
            v = _build_settings_view()
        else:
            v = ft.Text(f"View '{key}' not implemented yet", size=14, color="grey")

        view_cache[key] = v
        return v

    # ── Navigation handler ──
    def _navigate(key):
        nonlocal active_key
        active_key = key

        # Rebuild sidebar to highlight new active item
        sidebar_container.content = build_sidebar(active_key, _navigate, state)

        # Swap content
        view = _get_view(key)
        content_container.content = view

        # Show/hide preview panel
        if key in PREVIEW_VIEWS:
            preview_container.width = 370
            preview_container.content = preview_widget
            preview_container.visible = True
        else:
            preview_container.width = 0
            preview_container.content = None
            preview_container.visible = False

        page.update()

    # ── Language Selector ──
    def on_lang_change(e):
        state.set_language(lang_dropdown.value)
        view_cache.clear()
        _navigate(active_key)

    lang_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("de", "Deutsch"),
        ],
        value=state.language,
        width=110,
        content_padding=ft.Padding(8, 0, 8, 0),
        text_size=12, border_radius=6,
        on_change=on_lang_change,
    )

    # ── Backup / Restore ──
    def handle_backup_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        ok, msg = backup_tool.export_to_json(e.path)
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor="green" if ok else "red")
        page.snack_bar.open = True
        page.update()

    def handle_restore_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        filepath = e.files[0].path
        ok, msg = backup_tool.import_from_json(filepath)
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor="green" if ok else "red")
        page.snack_bar.open = True
        page.update()
        if ok:
            view_cache.clear()
            _navigate(active_key)

    backup_picker = ft.FilePicker(on_result=handle_backup_result)
    restore_picker = ft.FilePicker(on_result=handle_restore_result)
    page.overlay.extend([backup_picker, restore_picker])
    page.update()

    # ── Settings view ──
    def _build_settings_view():
        return ft.Container(
            expand=True,
            padding=ft.padding.only(left=36, right=36, top=28, bottom=20),
            content=ft.Column([
                ft.Text(state.t("header.settings_backup"), size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                ft.Text(state.t("subtitle.settings_backup"),
                         color=TEXT_MUTED, size=13),
                ft.Container(height=16),

                # Connection info
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(state.t("header.connection_status"), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Container(height=8),
                            ft.Row([
                                ft.Container(width=8, height=8, border_radius=4,
                                             bgcolor="#00c853" if state.api_connected else "#ef4444"),
                                ft.Text(f"{state.t('label.fastapi')}: {state.t('status.connected_simple') if state.api_connected else state.t('status.disconnected_simple')}",
                                         size=13, color=TEXT_PRIMARY),
                            ], spacing=8),
                            ft.Row([
                                ft.Container(width=8, height=8, border_radius=4,
                                             bgcolor="#00c853" if state.wallet_connected else "#ef4444"),
                                ft.Text(f"{state.t('label.google_wallet')}: {state.t('status.connected_simple') if state.wallet_connected else state.t('status.disconnected_simple')}",
                                         size=13, color=TEXT_PRIMARY),
                            ], spacing=8),
                        ], spacing=4),
                        padding=20,
                    ),
                    elevation=0, color="white",
                ),
                ft.Container(height=12),

                # Language
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(state.t("header.language_sprache"), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Container(height=8),
                            lang_dropdown,
                        ], spacing=4),
                        padding=20,
                    ),
                    elevation=0, color="white",
                ),
                ft.Container(height=12),

                # Backup / Restore
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(state.t("header.db_backup_restore"), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Container(height=8),
                            ft.Text(state.t("subtitle.db_backup_restore"),
                                     size=12, color=TEXT_MUTED),
                            ft.Container(height=12),
                            ft.Row([
                                ft.ElevatedButton(
                                    state.t("btn.backup_db"), icon=ft.Icons.DOWNLOAD,
                                    bgcolor=PRIMARY, color="white", height=40,
                                    on_click=lambda _: backup_picker.save_file(
                                        allowed_extensions=["json"], file_name="wallet_backup.json",
                                    ),
                                ),
                                ft.OutlinedButton(
                                    state.t("btn.restore_db"), icon=ft.Icons.UPLOAD, height=40,
                                    on_click=lambda _: restore_picker.pick_files(
                                        allowed_extensions=["json"],
                                    ),
                                ),
                            ], spacing=12),
                        ], spacing=4),
                        padding=20,
                    ),
                    elevation=0, color="white",
                ),
            ], scroll=ft.ScrollMode.AUTO),
        )

    # ── Top bar ──
    top_bar = ft.Container(
        height=48, bgcolor="white",
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        padding=ft.padding.symmetric(horizontal=20),
        content=ft.Row([
            ft.Text(state.t("header.dashboard_title"), size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(expand=True),
            ft.Row([
                ft.Container(width=8, height=8, border_radius=4,
                             bgcolor="#00c853" if state.api_connected else "#ef4444"),
                ft.Text("API", size=10, color=TEXT_MUTED),
                ft.Container(width=8, height=8, border_radius=4,
                             bgcolor="#00c853" if state.wallet_connected else "#ef4444"),
                ft.Text("Wallet", size=10, color=TEXT_MUTED),
            ], spacing=6),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )

    # ── Initial render ──
    sidebar_container.content = build_sidebar(active_key, _navigate, state)
    content_container.content = _get_view(active_key)
    preview_container.width = 370 if active_key in PREVIEW_VIEWS else 0
    preview_container.visible = active_key in PREVIEW_VIEWS
    if active_key in PREVIEW_VIEWS:
        preview_container.content = preview_widget

    # ── Main layout ──
    main_row = ft.Row([
        sidebar_container,
        ft.Column([
            top_bar,
            ft.Row([
                content_container,
                # Preview panel (right side, only for generator/manage views)
                ft.Container(
                    content=preview_container,
                    bgcolor=BG_COLOR,
                    padding=ft.padding.only(top=10, right=10, bottom=10),
                    border=ft.border.only(left=ft.BorderSide(1, BORDER_COLOR)),
                ),
            ], expand=True, spacing=0),
        ], expand=True, spacing=0),
    ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

    return [main_row]
