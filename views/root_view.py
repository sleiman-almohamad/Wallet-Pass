"""
Root View
Assembles the top-level header, status bar, and tab container.
"""

import flet as ft
from ui.class_builder import create_template_builder
from ui.pass_generator import create_pass_generator
from views.manage_templates_view import build_manage_templates_view
from views.manage_passes_view import build_manage_passes_view
from views.send_notification_view import build_send_notification_view
from utils.db_backup_tool import DatabaseBackupTool


def build_root_view(page: ft.Page, state) -> list:
    """
    Build every top-level control that gets added to ``page``.

    Returns a list of Flet controls: [header, status_bar, divider, tabs].
    """
    api_client = state.api_client
    wallet_client = state.wallet_client
    backup_tool = DatabaseBackupTool()

    # ── Helper: rebuild all tab views ──
    def _rebuild_views():
        """Re-create every tab's content and refresh status indicators."""
        nonlocal template_builder, pass_generator, manage_templates, manage_passes, send_notification

        template_builder = create_template_builder(page, state, api_client=api_client)
        pass_generator = create_pass_generator(page, state, api_client=api_client, wallet_client=wallet_client)
        manage_templates = build_manage_templates_view(page, state, api_client)
        manage_passes = build_manage_passes_view(page, state, api_client)
        send_notification = build_send_notification_view(page, state, api_client)

        tabs.tabs[0].text = state.t("tab.template_builder")
        tabs.tabs[0].content = template_builder

        tabs.tabs[1].text = state.t("tab.pass_generator")
        tabs.tabs[1].content = pass_generator

        tabs.tabs[2].text = state.t("tab.manage_templates")
        tabs.tabs[2].content = manage_templates

        tabs.tabs[3].text = state.t("tab.manage_passes")
        tabs.tabs[3].content = manage_passes

        tabs.tabs[4].text = state.t("tab.send_notification")
        tabs.tabs[4].content = send_notification

        # Connection status
        if state.wallet_connected:
            connection_status.value = state.t("status.connected")
            connection_status.color = "green"
        else:
            connection_status.value = state.t("status.not_connected")
            connection_status.color = "red"

        health = state.check_api_health()
        if state.api_connected:
            api_status.value = state.t("status.api_connected")
            api_status.color = "green"
        else:
            detail = health.get("database", health.get("detail", "unknown"))
            api_status.value = state.t("status.api_error", detail=detail)
            api_status.color = "orange"

        page.update()

    # ── Language Selector ──
    def on_lang_change(e):
        state.set_language(lang_dropdown.value)
        _rebuild_views()

    lang_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("de", "Deutsch"),
        ],
        value=state.language,
        width=120,
        content_padding=ft.Padding(10, 0, 10, 0),
        on_change=on_lang_change,
    )

    # ── Backup / Restore FilePickers ──
    def handle_backup_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        ok, msg = backup_tool.export_to_json(e.path)
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor="green" if ok else "red",
        )
        page.snack_bar.open = True
        page.update()

    def handle_restore_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        filepath = e.files[0].path
        ok, msg = backup_tool.import_from_json(filepath)
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor="green" if ok else "red",
        )
        page.snack_bar.open = True
        page.update()
        if ok:
            _rebuild_views()

    backup_picker = ft.FilePicker(on_result=handle_backup_result)
    restore_picker = ft.FilePicker(on_result=handle_restore_result)

    page.overlay.append(backup_picker)
    page.overlay.append(restore_picker)
    page.update()

    # ── Backup / Restore Menu ──
    backup_menu = ft.PopupMenuButton(
        icon=ft.Icons.SETTINGS_BACKUP_RESTORE,
        tooltip="Backup / Restore",
        items=[
            ft.PopupMenuItem(
                text="Backup Database",
                icon=ft.Icons.DOWNLOAD,
                on_click=lambda _: backup_picker.save_file(
                    allowed_extensions=["json"],
                    file_name="wallet_backup.json",
                ),
            ),
            ft.PopupMenuItem(
                text="Restore Database",
                icon=ft.Icons.UPLOAD,
                on_click=lambda _: restore_picker.pick_files(
                    allowed_extensions=["json"],
                ),
            ),
        ],
    )

    # ── Connection status indicators ──
    if state.wallet_connected:
        connection_status = ft.Text(state.t("status.connected"), color="green", size=12)
    else:
        connection_status = ft.Text(state.t("status.not_connected"), color="red", size=12)

    health = state.check_api_health()
    if state.api_connected:
        api_status = ft.Text(state.t("status.api_connected"), color="green", size=12)
    else:
        detail = health.get("database", health.get("detail", "unknown"))
        api_status = ft.Text(state.t("status.api_error", detail=detail), color="orange", size=12)

    # ── Tab contents ──
    template_builder = create_template_builder(page, state, api_client=api_client)
    pass_generator = create_pass_generator(page, state, api_client=api_client, wallet_client=wallet_client)
    manage_templates = build_manage_templates_view(page, state, api_client)
    manage_passes = build_manage_passes_view(page, state, api_client)
    send_notification = build_send_notification_view(page, state, api_client)

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text=state.t("tab.template_builder"), content=template_builder),
            ft.Tab(text=state.t("tab.pass_generator"), content=pass_generator),
            ft.Tab(text=state.t("tab.manage_templates"), content=manage_templates),
            ft.Tab(text=state.t("tab.manage_passes"), icon="contact_page", content=manage_passes),
            ft.Tab(text=state.t("tab.send_notification"), content=send_notification),
        ],
        expand=True,
    )

    # ── Assemble top-level controls ──
    return [
        ft.Row([
            ft.Image(src="B2F.png", width=150, height=150),
            ft.VerticalDivider(width=20, color="transparent"),
            ft.Column([
                ft.Text("Language / Sprache", size=10, color="grey"),
                lang_dropdown,
            ], spacing=2),
            backup_menu,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Row([connection_status, ft.Text(" | "), api_status]),
        ft.Divider(),
        tabs,
    ]
