"""
Live Preview Component
Displays a real-time visual preview of the Google Wallet pass
"""

import flet as ft


class LivePreview(ft.UserControl):
    """
    Real-time visual preview of a Google Wallet pass
    Updates automatically when template state changes
    """
    
    def __init__(self, template_state):
        super().__init__()
        self.template_state = template_state
        # Subscribe to state changes
        self.template_state.subscribe(self._on_state_change)
    
    def _on_state_change(self, data):
        """Called when template state changes"""
        if self.page:
            self.update()
    
    def build(self):
        """Build the pass preview"""
        data = self.template_state.get_all()
        
        # Extract data
        header = data.get("header", "Business Name")
        card_title = data.get("card_title", "Pass Title")
        bg_color = data.get("background_color", "#4285f4")
        logo_url = data.get("logo_url")
        hero_url = data.get("hero_url")
        fields = data.get("fields", [])
        
        return ft.Container(
            width=350,
            content=self._build_pass_card(
                header, card_title, bg_color, logo_url, hero_url, fields
            ),
            alignment=ft.alignment.center
        )
    
    def _build_pass_card(self, header, card_title, bg_color, logo_url, hero_url, fields):
        """Build the mobile-style pass card"""
        
        # Logo section
        logo_control = self._build_logo(logo_url)
        
        # Hero image section
        hero_control = self._build_hero(hero_url)
        
        # Fields section
        fields_control = self._build_fields(fields)
        
        return ft.Container(
            bgcolor=bg_color,
            border_radius=15,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(
                blur_radius=15,
                color="black26",
                offset=ft.Offset(0, 5)
            ),
            content=ft.Column([
                # Top Section: Logo & Header
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        logo_control,
                        ft.Container(width=10),  # Spacing
                        ft.Text(
                            header,
                            color="white",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            expand=True
                        )
                    ], alignment=ft.MainAxisAlignment.START)
                ),
                
                # Card Title Section
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(
                        card_title,
                        color="white",
                        size=22,
                        weight=ft.FontWeight.BOLD
                    )
                ),
                
                # Hero Image Section
                hero_control,
                
                # Bottom Section: QR & Details
                ft.Container(
                    bgcolor="white",
                    padding=15,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=12),
                        ft.Container(height=5),
                        ft.Row([
                            # QR Code placeholder
                            ft.Container(
                                width=80,
                                height=80,
                                bgcolor="grey200",
                                border_radius=5,
                                content=ft.Icon(
                                    ft.icons.QR_CODE_2,
                                    size=60,
                                    color="grey"
                                ),
                                alignment=ft.alignment.center
                            ),
                            ft.Container(width=15),
                            # Fields display
                            ft.Column([
                                fields_control
                            ], expand=True)
                        ], alignment=ft.MainAxisAlignment.START)
                    ])
                )
            ], spacing=0)
        )
    
    def _build_logo(self, logo_url):
        """Build logo display"""
        if logo_url:
            return ft.Container(
                width=50,
                height=50,
                border_radius=25,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(
                    src=logo_url,
                    width=50,
                    height=50,
                    fit=ft.ImageFit.COVER
                )
            )
        else:
            # Placeholder
            return ft.Container(
                width=50,
                height=50,
                border_radius=25,
                bgcolor="white30",
                content=ft.Icon(
                    ft.icons.BUSINESS,
                    color="white",
                    size=30
                ),
                alignment=ft.alignment.center
            )
    
    def _build_hero(self, hero_url):
        """Build hero image display"""
        if hero_url:
            return ft.Container(
                height=150,
                content=ft.Image(
                    src=hero_url,
                    width=350,
                    height=150,
                    fit=ft.ImageFit.COVER
                )
            )
        else:
            # Placeholder
            return ft.Container(
                height=150,
                bgcolor="black12",
                content=ft.Column([
                    ft.Icon(ft.icons.IMAGE, size=40, color="grey"),
                    ft.Text("Hero Image", size=12, color="grey")
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
    
    def _build_fields(self, fields):
        """Build custom fields display"""
        if not fields:
            return ft.Column([
                ft.Text("John Doe", weight=ft.FontWeight.BOLD, size=14, color="black"),
                ft.Text("ID: 1234567890", size=12, color="grey")
            ])
        
        # Display first 3 fields
        field_widgets = []
        for field in fields[:3]:
            field_widgets.append(
                ft.Text(
                    f"{field.get('label', 'Field')}: Sample",
                    size=12,
                    color="black" if field_widgets == [] else "grey"
                )
            )
        
        return ft.Column(field_widgets, spacing=3)
