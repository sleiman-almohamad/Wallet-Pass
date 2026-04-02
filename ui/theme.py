"""
UI Theme — Design Tokens & Helper Components
Centralised SaaS design-system constants and reusable builders.
"""

import flet as ft

# ─────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────
BG_COLOR       = "#f5f5f7"
CARD_BG        = "#ffffff"
CARD_RADIUS    = 12
SIDEBAR_WIDTH  = 270
PRIMARY        = "#0052FF"
PRIMARY_LIGHT  = "#e8eeff"
ACCENT_GREEN   = "#00c853"
TEXT_PRIMARY    = "#1a1a2e"
TEXT_SECONDARY  = "#6b7280"
TEXT_MUTED     = "#9ca3af"
BORDER_COLOR   = "#e5e7eb"
SHADOW_COLOR   = "#0000000d"
SECTION_HEADER = "#374151"


# ─────────────────────────────────────────────────────────
# HELPER: Section Card
# ─────────────────────────────────────────────────────────
def card(content, **kwargs):
    """Wrap *content* in a styled white Card with soft shadow."""
    return ft.Card(
        content=ft.Container(content=content, padding=28, **kwargs),
        elevation=0,
        color=CARD_BG,
        surface_tint_color=CARD_BG,
        shadow_color=SHADOW_COLOR,
    )


def section_title(text, icon=None):
    """Accent-coloured section header, optionally with a leading icon."""
    row = [ft.Text(text, size=14, weight=ft.FontWeight.W_700, color=PRIMARY)]
    if icon:
        row.insert(0, ft.Icon(icon, size=16, color=PRIMARY))
    return ft.Container(
        content=ft.Row(row, spacing=8),
        padding=ft.padding.only(top=8, bottom=4),
    )
