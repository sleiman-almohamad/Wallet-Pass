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
                            bgcolor="#121212",
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=self._render_screen(),
                        ),
                        # Status bar overlay
                        ft.Container(
                            alignment=ft.alignment.top_center,
                            padding=ft.padding.only(left=26, right=24, top=16),
                            content=ft.Row([
                                ft.Text("9:41", size=11, weight=ft.FontWeight.W_700, color="white"),
                            ], spacing=4),
                        ),
                        # Notch / Dynamic Island
                        ft.Container(
                            content=ft.Container(width=94, height=26, border_radius=13,
                                                 bgcolor="#1a1a1a"),
                            alignment=ft.alignment.top_center,
                            padding=ft.padding.only(top=10),
                        ),
                        # Home Indicator
                        ft.Container(
                            alignment=ft.alignment.bottom_center,
                            padding=ft.padding.only(bottom=10),
                            content=ft.Container(width=110, height=4, border_radius=2, bgcolor="white40")
                        )
                    ]),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(top=30, bottom=20),
        )

    # ── renderers ───────────────────────────────────────
    def _render_screen(self) -> ft.Control:
        if self._platform == "apple":
            return self._apple_card()
        return self._google_card()

    def _google_card(self) -> ft.Control:
        d = self._data
        bg_color = d.get("bg_color", "#4285f4")
        logo_url = d.get("logo_url")
        hero_url = d.get("hero_image_url")
        card_title = d.get("issuer_name", "Wallet Pass")
        holder_name = d.get("holder_name", "Holder Name")

        # 1. Dynamic Text Modules Extraction
        text_modules = d.get("textModulesData", [])
        if not text_modules:
            # Fallback to manual row inputs from the generator UI if no JSON modules exist yet
            for i in range(5):
                for pos in ["left", "middle", "right"]:
                    val = d.get(f"row_{i}_{pos}")
                    if val:
                        text_modules.append({"header": f"{pos.upper()} {i+1}", "body": val})

        # Prepare modules in rows (max 3 per row)
        module_rows = []

        # Top-level header/subheader if present
        top_header = d.get("header", d.get("header_text"))
        top_subheader = d.get("subheader", d.get("subheader_text"))
        if top_header or top_subheader:
            header_col = []
            if top_subheader:
                header_col.append(ft.Text(top_subheader, size=13, color="white", weight=ft.FontWeight.W_500))
            if top_header:
                header_col.append(ft.Text(top_header, size=20, color="white", weight=ft.FontWeight.W_400))
            module_rows.append(ft.Container(content=ft.Column(header_col, spacing=2), padding=ft.padding.only(bottom=16)))

        current_row = []
        for module in text_modules:
            header = module.get("header", "")
            body = module.get("body", "")
            m_type = module.get("module_type", module.get("type", "text"))

            if m_type == "link":
                # Render as a sleek button for external links
                col = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LANGUAGE, color="white", size=11),
                        ft.Text(header or "Open Link", size=11, color="white", weight=ft.FontWeight.W_600),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor="#1A73E8",
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=18,
                    expand=True,
                    margin=ft.margin.only(top=4)
                )
            else:
                col = ft.Column([
                    ft.Text(header.upper() if header else "", size=10, color="white70", weight=ft.FontWeight.W_500),
                    ft.Text(body or "—", size=14, color="white", weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=2, tight=True, expand=True)

            current_row.append(col)
            if len(current_row) == 3:
                module_rows.append(ft.Row(current_row, spacing=20, alignment=ft.MainAxisAlignment.START))
                current_row = []

        if current_row:
            module_rows.append(ft.Row(current_row, spacing=20, alignment=ft.MainAxisAlignment.START))

        # 2. Build UI Components
        # Header Row
        header_section = ft.Container(
            padding=ft.padding.only(left=20, right=20, top=20, bottom=14),
            content=ft.Row([
                ft.Container(
                    width=40, height=40, border_radius=20,
                    bgcolor="white24" if not logo_url else None,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(src=logo_url, fit=ft.ImageFit.COVER) if logo_url else ft.Icon(ft.Icons.IMAGE, color="white30", size=20),
                ),
                ft.Text(card_title, size=16, weight=ft.FontWeight.W_600, color="white", expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        )

        # Hero Image Section (Edge-to-Edge - Google Standard)
        hero_section = ft.Container()
        if hero_url:
            hero_section = ft.Container(
                width=float('inf'),
                height=130,
                content=ft.Image(src=hero_url, fit=ft.ImageFit.COVER)
            )

        # Text Modules Section
        modules_section = ft.Container(
            width=float("inf"),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            content=ft.Column(module_rows, spacing=16) if module_rows else ft.Text("No fields added", color="white30", size=11, italic=True),
            expand=True,
        )

        # Barcode Section (Pure White Area)
        barcode_section = ft.Container(
            bgcolor="white",
            width=float("inf"),
            padding=ft.padding.symmetric(vertical=20),
            content=ft.Column([
                ft.Image(src="https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg", width=90, height=90, fit=ft.ImageFit.CONTAIN),
                ft.Text(holder_name, size=14, color="grey700", weight=ft.FontWeight.W_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            alignment=ft.alignment.center
        )

        # Main Card Container
        google_wallet_card = ft.Container(
            bgcolor=bg_color,
            width=float("inf"),
            border_radius=24,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column([
                header_section,
                hero_section,
                modules_section,
                barcode_section,
            ], spacing=0)
        )

        return ft.Container(
            expand=True,
            bgcolor="#15171A",
            content=ft.Column([
                ft.Container(
                    padding=ft.padding.only(left=22, top=45, bottom=6),
                    content=ft.Text("Google Wallet", size=15, weight=ft.FontWeight.W_500, color="white30")
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=google_wallet_card
                )
            ])
        )

    def _apple_card(self) -> ft.Control:
        d = self._data
        bg = d.get("bg_color", "#1a1a2e")
        fg = d.get("fg_color", "#ffffff")
        lbl_clr = d.get("label_color", "#bbbbbb")
        org = d.get("org_name") or d.get("organization_name") or "Organization"
        logo_text = d.get("logo_text") or "PASS"
        strip_url = d.get("strip_url")
        holder = d.get("holder_name") or "Holder Name"
        
        ticket_layout = "strip" if bool(strip_url) else "background"
        bg_image_url = d.get("background_image_url")
        thumbnail_url = d.get("thumbnail_url")

        # Fields
        def _field_row(label, value):
            if not label and not value:
                return ft.Container()
            return ft.Column([
                ft.Text((label or "LABEL").upper(), size=10, color=lbl_clr,
                        weight=ft.FontWeight.W_600, style=ft.TextStyle(letter_spacing=1)),
                ft.Text(value or "—", size=16, color=fg, weight=ft.FontWeight.BOLD),
            ], spacing=2, tight=True)

        dynamic_fields = d.get("dynamic_fields", [])
        
        header_controls = []
        primary_controls = []
        secondary_controls = []
        auxiliary_controls = []
        
        for f in dynamic_fields:
            ftype = f.get("field_type")
            f_widget = _field_row(f.get("label"), f.get("value"))
            if ftype == "header":
                header_controls.append(f_widget)
            elif ftype == "primary":
                primary_controls.append(f_widget)
            elif ftype == "secondary":
                secondary_controls.append(f_widget)
            elif ftype == "auxiliary":
                auxiliary_controls.append(f_widget)

        # Apple cards show primary on its own row, then secondary/auxiliary usually in row formatting depending on space.
        # We will wrap them in rows to match the typical Apple pass layout: secondary fields on one line, auxiliary on another line below.
        header_row = ft.Row(header_controls, spacing=14) if header_controls else ft.Container()
        primary_row = ft.Row(primary_controls, spacing=14) if primary_controls else ft.Container()
        secondary_row = ft.Row(secondary_controls, spacing=14, wrap=True) if secondary_controls else ft.Container()
        auxiliary_row = ft.Row(auxiliary_controls, spacing=14, wrap=True) if auxiliary_controls else ft.Container()

        strip_widget = (
            ft.Image(src=strip_url, fit=ft.ImageFit.COVER, height=130, width=float("inf"))
            if strip_url
            else ft.Container(height=110, bgcolor="black12",
                              content=ft.Column([
                                  ft.Icon(ft.Icons.PANORAMA, size=32, color="white30"),
                                  ft.Text("Strip Image", size=11, color="white30"),
                              ], alignment=ft.MainAxisAlignment.CENTER,
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        )

        thumbnail_widget = ft.Image(src=thumbnail_url, fit=ft.ImageFit.CONTAIN, height=60) if thumbnail_url else ft.Container()

        logo_row = ft.Container(
            padding=ft.padding.only(left=20, right=20, top=16, bottom=12),
            content=ft.Row([
                ft.Text(logo_text, size=18, weight=ft.FontWeight.BOLD, color=fg,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(expand=True),
                header_row if header_controls else ft.Text(org, size=12, color=lbl_clr),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

        barcode_section = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(vertical=20),
            content=ft.Column([
                ft.Icon(ft.Icons.QR_CODE_2, size=80, color="black"),
                ft.Text(holder, size=14, color="grey700", weight=ft.FontWeight.W_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            alignment=ft.alignment.center
        )

        if ticket_layout == "background":
            card_content = ft.Column([
                logo_row,
                ft.Container(
                   padding=ft.padding.symmetric(horizontal=20),
                   content=ft.Row([ft.Container(expand=True), thumbnail_widget]),
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    content=ft.Column([
                        primary_row,
                        secondary_row,
                        auxiliary_row
                    ], spacing=14),
                ),
                barcode_section
            ], spacing=0)
        else: # strip layout
            card_content = ft.Column([
                logo_row,
                ft.Container(
                    padding=ft.padding.only(left=20, right=20, bottom=12),
                    content=primary_row,
                ),
                strip_widget,
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    content=ft.Column([
                        secondary_row,
                        auxiliary_row
                    ], spacing=14),
                ),
                barcode_section
            ], spacing=0)

        apple_wallet_card = ft.Container(
            bgcolor=bg,
            border_radius=18,
            image=ft.DecorationImage(src=bg_image_url, fit=ft.ImageFit.COVER) if (ticket_layout == "background" and bg_image_url) else None,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=card_content
        )

        return ft.Container(
            expand=True,
            bgcolor="black",
            content=ft.Column([
                ft.Container(
                    padding=ft.padding.only(left=22, top=45, bottom=6),
                    content=ft.Text("Apple Wallet", size=15, weight=ft.FontWeight.W_500, color="white30")
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=apple_wallet_card
                )
            ])
        )
