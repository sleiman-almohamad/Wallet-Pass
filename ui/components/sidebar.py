"""
Categorised Navigation Sidebar
Groups nav items under Google Wallet, Apple Wallet, Notifications, and System.
"""

import flet as ft
from ui.theme import (
    SIDEBAR_WIDTH, PRIMARY, PRIMARY_LIGHT, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR,
)


# ─────────────────────────────────────────────────────────
# NAV STRUCTURE
# ─────────────────────────────────────────────────────────
NAV_STRUCTURE = [
    {
        "category": "GOOGLE WALLET",
        "icon": ft.Icons.ACCOUNT_BALANCE_WALLET,
        "items": [
            {"key": "g_template_builder",  "label": "Template Builder",  "icon": ft.Icons.EDIT_DOCUMENT},
            {"key": "g_manage_templates",  "label": "Manage Templates",  "icon": ft.Icons.STYLE},
            {"key": "g_pass_generator",    "label": "Pass Generator",    "icon": ft.Icons.DYNAMIC_FORM},
            {"key": "g_manage_passes",     "label": "Manage Passes",     "icon": ft.Icons.CREDIT_CARD},
        ],
    },
    {
        "category": "APPLE WALLET",
        "icon": ft.Icons.PHONE_IPHONE,
        "items": [
            {"key": "a_template_builder", "label": "Template Builder", "icon": ft.Icons.EDIT_DOCUMENT},
            {"key": "a_manage_templates", "label": "Manage Templates", "icon": ft.Icons.STYLE},
            {"key": "a_pass_generator",    "label": "Pass Generator",    "icon": ft.Icons.DYNAMIC_FORM},
            {"key": "a_manage_passes",     "label": "Manage Passes",     "icon": ft.Icons.CREDIT_CARD},
        ],
    },
    {
        "category": "DISTRIBUTION",
        "icon": ft.Icons.QR_CODE_SCANNER,
        "items": [
            {"key": "qr_campaigns", "label": "QR Campaigns", "icon": ft.Icons.QR_CODE_2},
        ],
    },
    {
        "category": "NOTIFICATIONS",
        "icon": ft.Icons.MARK_EMAIL_UNREAD_OUTLINED,
        "items": [
            {"key": "notifications", "label": "Notification Center", "icon": ft.Icons.NOTIFICATIONS_ACTIVE},
        ],
    },
    {
        "category": "SYSTEM",
        "icon": ft.Icons.SETTINGS,
        "items": [
            {"key": "settings", "label": "Settings & Backup", "icon": ft.Icons.TUNE},
        ],
    },
]

# Views that get a live-preview panel on the right
PREVIEW_VIEWS = {
    "g_pass_generator", "a_pass_generator",
    "g_manage_passes",  "a_manage_passes"
}


def build_sidebar(active_key: str, on_navigate, state=None):
    """
    Return the sidebar Container with grouped nav items.

    Args:
        active_key:  currently selected nav key (e.g. ``"g_pass_generator"``)
        on_navigate: callback ``fn(key: str)`` called when a nav item is clicked
        state:       optional AppState, used for connection-status indicators
    """
    controls: list = [
        # Brand header
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=38, height=38, border_radius=10,
                        gradient=ft.LinearGradient(
                            colors=[PRIMARY, "#6366f1"],
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                        ),
                        content=ft.Icon(ft.Icons.WALLET, color="white", size=20),
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text("WalletPass", size=17, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                        ft.Text("Management Suite", size=10, color=TEXT_MUTED),
                    ], spacing=0),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ]),
            padding=ft.padding.only(left=22, right=22, top=20, bottom=28),
        ),
    ]

    for group in NAV_STRUCTURE:
        # Category header
        controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(group["icon"], size=14, color=TEXT_MUTED),
                    ft.Text(group["category"], size=10, weight=ft.FontWeight.W_700,
                            color=TEXT_MUTED, style=ft.TextStyle(letter_spacing=1.2)),
                ], spacing=6),
                padding=ft.padding.only(left=22, top=18, bottom=6),
            )
        )

        for item in group["items"]:
            is_active = item["key"] == active_key
            controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(item["icon"], size=18,
                                color=PRIMARY if is_active else TEXT_SECONDARY),
                        ft.Text(item["label"], size=13,
                                color=TEXT_PRIMARY if is_active else TEXT_SECONDARY,
                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL),
                    ], spacing=12),
                    padding=ft.padding.only(left=22, top=10, bottom=10, right=12),
                    bgcolor=PRIMARY_LIGHT if is_active else None,
                    border=ft.border.only(left=ft.BorderSide(3, PRIMARY)) if is_active else None,
                    border_radius=ft.border_radius.only(top_right=8, bottom_right=8),
                    on_click=lambda _, k=item["key"]: on_navigate(k),
                    ink=True,
                    animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                )
            )

    # Spacer + footer
    controls.append(ft.Container(expand=True))
    controls.append(ft.Divider(height=1, color=BORDER_COLOR))

    # Connection status (if state available)
    if state is not None:
        wallet_ok = getattr(state, "wallet_connected", False)
        api_ok    = getattr(state, "api_connected", False)

        def _dot(ok):
            return ft.Container(width=8, height=8, border_radius=4,
                                bgcolor="#00c853" if ok else "#ef4444")

        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([_dot(api_ok), ft.Text("API", size=10, color=TEXT_MUTED)], spacing=6),
                    ft.Row([_dot(wallet_ok), ft.Text("Wallet", size=10, color=TEXT_MUTED)], spacing=6),
                ], spacing=4),
                padding=ft.padding.only(left=22, right=22, top=8, bottom=4),
            )
        )

    controls.append(
        ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Text("SM", size=12, weight=ft.FontWeight.BOLD),
                    bgcolor=PRIMARY, color="white", radius=16,
                ),
                ft.Column([
                    ft.Text("Admin User", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Text("admin@walletpass.io", size=10, color=TEXT_MUTED),
                ], spacing=0),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=22, right=22, top=12, bottom=4),
        )
    )

    # Company Logo at the very bottom
    controls.append(
        ft.Container(
            content=ft.Image(
                src="B2F.png",
                width=SIDEBAR_WIDTH,
                fit=ft.ImageFit.FIT_WIDTH,
                filter_quality=ft.FilterQuality.HIGH,
            ),
            padding=ft.padding.only(bottom=0, top=10),
            alignment=ft.alignment.bottom_center,
        )
    )

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor="white",
        border=ft.border.only(right=ft.BorderSide(1, BORDER_COLOR)),
        content=ft.Column(controls, spacing=2, scroll=ft.ScrollMode.AUTO),
    )
