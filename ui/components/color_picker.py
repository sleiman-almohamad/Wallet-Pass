"""
Color Picker Component
Visual color selection for pass background customization
"""

import flet as ft


class ColorPicker(ft.UserControl):
    """
    Color picker with preset palette and custom hex input
    """
    
    # Material Design color palette
    PRESET_COLORS = [
        {"name": "Google Blue", "hex": "#4285f4"},
        {"name": "Red", "hex": "#EA4335"},
        {"name": "Yellow", "hex": "#FBBC04"},
        {"name": "Green", "hex": "#34A853"},
        {"name": "Purple", "hex": "#9C27B0"},
        {"name": "Orange", "hex": "#FF6F00"},
        {"name": "Cyan", "hex": "#00BCD4"},
        {"name": "Blue Grey", "hex": "#607D8B"},
        {"name": "Teal", "hex": "#009688"},
        {"name": "Indigo", "hex": "#3F51B5"},
        {"name": "Pink", "hex": "#E91E63"},
        {"name": "Deep Orange", "hex": "#FF5722"},
    ]
    
    def __init__(self, template_state):
        super().__init__()
        self.template_state = template_state
        self.current_color = template_state.get("background_color", "#4285f4")
        self.hex_input = None
    
    def build(self):
        """Build the color picker UI"""
        
        # Hex input field
        self.hex_input = ft.TextField(
            label="Custom Hex Color",
            value=self.current_color,
            width=200,
            on_change=self._on_hex_change,
            prefix_text="#",
            max_length=6,
            hint_text="4285f4"
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Background Color", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                
                # Color swatches grid
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            self._create_color_swatch(color["hex"], color["name"])
                            for color in self.PRESET_COLORS[:6]
                        ], spacing=8),
                        ft.Column([
                            self._create_color_swatch(color["hex"], color["name"])
                            for color in self.PRESET_COLORS[6:]
                        ], spacing=8)
                    ], spacing=8),
                    padding=10,
                    bgcolor="grey100",
                    border_radius=8
                ),
                
                ft.Container(height=10),
                
                # Custom hex input
                self.hex_input,
                
                # Current color preview
                ft.Row([
                    ft.Text("Current:", size=12, color="grey"),
                    ft.Container(
                        width=40,
                        height=40,
                        bgcolor=self.current_color,
                        border_radius=20,
                        border=ft.border.all(2, "grey300")
                    )
                ], alignment=ft.MainAxisAlignment.START)
                
            ], spacing=10),
            padding=15,
            border=ft.border.all(1, "grey300"),
            border_radius=10
        )
    
    def _create_color_swatch(self, color_hex, color_name):
        """Create a clickable color swatch"""
        is_selected = color_hex == self.current_color
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    width=30,
                    height=30,
                    bgcolor=color_hex,
                    border_radius=15,
                    border=ft.border.all(
                        3 if is_selected else 1,
                        "white" if is_selected else "grey300"
                    ),
                    shadow=ft.BoxShadow(
                        blur_radius=5,
                        color="black26"
                    ) if is_selected else None
                ),
                ft.Text(
                    color_name,
                    size=11,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
                )
            ], spacing=8),
            on_click=lambda e, c=color_hex: self._on_color_select(c),
            ink=True,
            padding=5,
            border_radius=5
        )
    
    def _on_color_select(self, color_hex):
        """Handle color swatch selection"""
        self.current_color = color_hex
        self.hex_input.value = color_hex.replace("#", "")
        self.template_state.update("background_color", color_hex)
        self.update()
    
    def _on_hex_change(self, e):
        """Handle custom hex input"""
        hex_value = e.control.value.strip()
        
        # Remove # if user typed it
        if hex_value.startswith("#"):
            hex_value = hex_value[1:]
        
        # Validate hex color (6 characters, valid hex)
        if len(hex_value) == 6:
            try:
                # Validate it's a valid hex color
                int(hex_value, 16)
                color_hex = f"#{hex_value}"
                self.current_color = color_hex
                self.template_state.update("background_color", color_hex)
                self.update()
            except ValueError:
                # Invalid hex color, ignore
                pass
