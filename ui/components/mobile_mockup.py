"""
Mobile Mockup Preview Component
A realistic smartphone frame that renders a Google or Apple wallet pass preview.
Updates live as the user types in either generator form.
"""

import flet as ft
from ui.theme import ACCENT_GREEN, TEXT_MUTED, BORDER_COLOR


class MobileMockupPreview:
    """Realistic smartphone frame that renders a Google or Apple pass preview."""

    def __init__(self):
        self._container_ref = ft.Ref[ft.Container]()
        self._data: dict = {}
        self._platform: str = "google"

    # ── public API ──────────────────────────────────────
    def update_data(self, data: dict, platform: str = "google"):
        self._data = data
        self._platform = platform
        if self._container_ref.current:
            self._container_ref.current.content = self._render_screen()
            if self._container_ref.current.page:
                self._container_ref.current.update()

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(width=8, height=8, border_radius=4, bgcolor=ACCENT_GREEN),
                    ft.Text("LIVE PREVIEW", size=10, weight=ft.FontWeight.W_700,
                            color=TEXT_MUTED, style=ft.TextStyle(letter_spacing=2)),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                ft.Container(height=12),
                # Phone frame
                ft.Container(
                    width=310, height=620,
                    border_radius=40,
                    border=ft.border.all(6, "#1a1a1a"),
                    bgcolor="#1a1a1a",
                    shadow=ft.BoxShadow(blur_radius=30, spread_radius=2, color="black26",
                                        offset=ft.Offset(0, 10)),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Stack([
                        # Inner screen
                        ft.Container(
                            ref=self._container_ref,
                            margin=4,
                            border_radius=34,
                            bgcolor="#f0f0f0",
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=self._render_screen(),
                        ),
                        # Notch / Dynamic Island
                        ft.Container(
                            content=ft.Container(width=90, height=26, border_radius=13,
                                                 bgcolor="#1a1a1a"),
                            alignment=ft.alignment.top_center,
                            padding=ft.padding.only(top=8),
                        ),
                    ]),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(top=30, bottom=20),
        )

    # ── renderers ───────────────────────────────────────
    def _render_screen(self) -> ft.Column:
        if self._platform == "apple":
            return self._apple_card()
        return self._google_card()

    def _google_card(self) -> ft.Column:
        d = self._data
        bg = d.get("bg_color", "#4285f4")
        logo_url = d.get("logo_url")
        hero_url = d.get("hero_image_url") or d.get("hero_image")
        card_title = d.get("issuer_name") or d.get("card_title") or "Business Name"
        holder = d.get("holder_name") or "Holder Name"

        # Text module rows
        rows_ui = []
        for i in range(5):
            left  = d.get(f"row_{i}_left", "")
            mid   = d.get(f"row_{i}_middle", "")
            right = d.get(f"row_{i}_right", "")
            if left or mid or right:
                cols = []
                for val in [left, mid, right]:
                    if val:
                        cols.append(ft.Column([
                            ft.Text(val.upper()[:14], size=9, color="white70", weight=ft.FontWeight.W_500),
                            ft.Text("—", size=13, color="white", weight=ft.FontWeight.BOLD),
                        ], spacing=1, expand=True, tight=True))
                if cols:
                    rows_ui.append(ft.Row(cols, spacing=10))

        # Also render textModulesData if present
        text_modules = d.get("textModulesData", [])
        for module in text_modules:
            header = module.get("header", "")
            body = module.get("body", "")
            if header or body:
                rows_ui.append(ft.Row([
                    ft.Column([
                        ft.Text(header.upper()[:14] if header else "", size=9, color="white70", weight=ft.FontWeight.W_500),
                        ft.Text(body or "—", size=13, color="white", weight=ft.FontWeight.BOLD),
                    ], spacing=1, expand=True, tight=True),
                ], spacing=10))

        # Logo
        logo_widget = (
            ft.Container(width=36, height=36, border_radius=18, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                         content=ft.Image(src=logo_url, fit=ft.ImageFit.COVER))
            if logo_url
            else ft.Container(width=36, height=36, border_radius=18, bgcolor="white24",
                              content=ft.Icon(ft.Icons.BUSINESS, color="white70", size=18),
                              alignment=ft.alignment.center)
        )

        # Hero
        hero_widget = (
            ft.Container(height=110, margin=ft.margin.symmetric(horizontal=14),
                         border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                         content=ft.Image(src=hero_url, fit=ft.ImageFit.COVER),
                         shadow=ft.BoxShadow(blur_radius=8, color="black26"))
            if hero_url
            else ft.Container(height=80, margin=ft.margin.symmetric(horizontal=14),
                              border_radius=10, bgcolor="black12",
                              content=ft.Column([
                                  ft.Icon(ft.Icons.IMAGE, size=28, color="white30"),
                                  ft.Text("Hero Image", size=10, color="white30"),
                              ], alignment=ft.MainAxisAlignment.CENTER,
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        )

        return ft.Column([
            # Status bar spacer
            ft.Container(height=36, bgcolor=bg),
            # Header
            ft.Container(
                bgcolor=bg,
                padding=ft.padding.only(left=18, right=18, bottom=8),
                content=ft.Row([
                    logo_widget,
                    ft.Text(card_title, size=16, weight=ft.FontWeight.BOLD, color="white",
                            expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            # Hero
            ft.Container(bgcolor=bg, content=hero_widget),
            # Text modules
            ft.Container(
                bgcolor=bg,
                padding=ft.padding.symmetric(horizontal=18, vertical=12),
                content=ft.Column(rows_ui, spacing=10),
                expand=True,
            ),
            # Barcode section
            ft.Container(
                bgcolor="white",
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
                padding=ft.padding.only(top=14, bottom=18),
                content=ft.Column([
                    ft.Icon(ft.Icons.QR_CODE_2, size=64, color="black87"),
                    ft.Text(holder, size=13, color="black54", weight=ft.FontWeight.W_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            ),
        ], spacing=0, expand=True)

    def _apple_card(self) -> ft.Column:
        d = self._data
        bg = d.get("bg_color", "#1a1a2e")
        org = d.get("org_name") or d.get("organization_name") or "Organization"
        logo_text = d.get("logo_text") or "PASS"
        strip_url = d.get("strip_url")
        holder = d.get("holder_name") or "Holder Name"

        # Fields
        def _field_row(label, value):
            if not label and not value:
                return ft.Container()
            return ft.Column([
                ft.Text((label or "LABEL").upper(), size=9, color="white60",
                        weight=ft.FontWeight.W_600, style=ft.TextStyle(letter_spacing=1)),
                ft.Text(value or "—", size=15, color="white", weight=ft.FontWeight.BOLD),
            ], spacing=2, tight=True)

        primary   = _field_row(d.get("primary_label"), d.get("primary_value"))
        secondary = _field_row(d.get("secondary_label"), d.get("secondary_value"))
        auxiliary  = _field_row(d.get("auxiliary_label"), d.get("auxiliary_value"))

        strip_widget = (
            ft.Container(height=120, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                         content=ft.Image(src=strip_url, fit=ft.ImageFit.COVER))
            if strip_url
            else ft.Container(height=90, bgcolor="black12",
                              content=ft.Column([
                                  ft.Icon(ft.Icons.PANORAMA, size=28, color="white30"),
                                  ft.Text("Strip Image", size=10, color="white30"),
                              ], alignment=ft.MainAxisAlignment.CENTER,
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        )

        return ft.Column([
            ft.Container(height=36, bgcolor=bg),
            # Logo row
            ft.Container(
                bgcolor=bg,
                padding=ft.padding.symmetric(horizontal=18, vertical=6),
                content=ft.Row([
                    ft.Text(logo_text, size=17, weight=ft.FontWeight.BOLD, color="white",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(expand=True),
                    ft.Text(org, size=12, color="white70"),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            # Strip
            ft.Container(bgcolor=bg, content=strip_widget),
            # Fields
            ft.Container(
                bgcolor=bg,
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
                content=ft.Column([primary, secondary, auxiliary], spacing=12),
                expand=True,
            ),
            # Barcode
            ft.Container(
                bgcolor="white",
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
                padding=ft.padding.only(top=14, bottom=18),
                content=ft.Column([
                    ft.Icon(ft.Icons.QR_CODE_2, size=64, color="black87"),
                    ft.Text(holder, size=13, color="black54", weight=ft.FontWeight.W_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            ),
        ], spacing=0, expand=True)
