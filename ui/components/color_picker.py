"""
Color Picker Component
Visual color selection for pass background customization
"""

import flet as ft


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


def create_color_picker(page, color_state, on_change_callback):
    """
    Create a color picker component
    
    Args:
        page: Flet page instance
        color_state: State object with get/update methods
        on_change_callback: Function to call when color changes
        
    Returns:
        ft.Container with color picker UI
    """
    current_color = color_state.get("background_color", "#4285f4")
    
    # Create refs for controls that need updating
    hex_input_ref = ft.Ref[ft.TextField]()
    current_preview_ref = ft.Ref[ft.Container]()
    swatch_container_ref = ft.Ref[ft.Container]()
    
    def on_hex_change(e):
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
                color_state.update("background_color", color_hex)
                
                # Update preview
                if current_preview_ref.current:
                    current_preview_ref.current.bgcolor = color_hex
                    page.update()
                
                # Rebuild swatches to update selection
                rebuild_swatches()
                
                if on_change_callback:
                    on_change_callback()
            except ValueError:
                # Invalid hex color, ignore
                pass
    
    def on_color_select(color_hex):
        """Handle color swatch selection"""
        color_state.update("background_color", color_hex)
        hex_input_ref.current.value = color_hex.replace("#", "")
        
        # Update preview
        if current_preview_ref.current:
            current_preview_ref.current.bgcolor = color_hex
        
        # Rebuild swatches to update selection
        rebuild_swatches()
        
        page.update()
        
        if on_change_callback:
            on_change_callback()
    
    def create_color_swatch(color_hex, color_name):
        """Create a clickable color swatch"""
        current = color_state.get("background_color", "#4285f4")
        is_selected = color_hex == current
        
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
            on_click=lambda e, c=color_hex: on_color_select(c),
            ink=True,
            padding=5,
            border_radius=5
        )
    
    def rebuild_swatches():
        """Rebuild color swatches with updated selection"""
        if swatch_container_ref.current:
            swatch_container_ref.current.content = ft.Row([
                ft.Column([
                    create_color_swatch(color["hex"], color["name"])
                    for color in PRESET_COLORS[:6]
                ], spacing=8),
                ft.Column([
                    create_color_swatch(color["hex"], color["name"])
                    for color in PRESET_COLORS[6:]
                ], spacing=8)
            ], spacing=8)
            page.update()
    
    # Hex input field
    hex_input = ft.TextField(
        ref=hex_input_ref,
        label="Custom Hex Color",
        value=current_color.replace("#", ""),
        width=200,
        on_change=on_hex_change,
        prefix_text="#",
        max_length=6,
        hint_text="4285f4"
    )
    
    # Color swatches container
    swatch_container = ft.Container(
        ref=swatch_container_ref,
        content=ft.Row([
            ft.Column([
                create_color_swatch(color["hex"], color["name"])
                for color in PRESET_COLORS[:6]
            ], spacing=8),
            ft.Column([
                create_color_swatch(color["hex"], color["name"])
                for color in PRESET_COLORS[6:]
            ], spacing=8)
        ], spacing=8),
        padding=10,
        bgcolor="grey100",
        border_radius=8
    )
    
    # Current color preview
    current_preview = ft.Container(
        ref=current_preview_ref,
        width=40,
        height=40,
        bgcolor=current_color,
        border_radius=20,
        border=ft.border.all(2, "grey300")
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text("Background Color", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(height=5),
            
            # Color swatches grid
            swatch_container,
            
            ft.Container(height=10),
            
            # Custom hex input
            hex_input,
            
            # Current color preview
            ft.Row([
                ft.Text("Current:", size=12, color="grey"),
                current_preview
            ], alignment=ft.MainAxisAlignment.START)
            
        ], spacing=10),
        padding=15,
        border=ft.border.all(1, "grey300"),
        border_radius=10
    )


# Legacy compatibility - create a simple wrapper class
class ColorPicker:
    """Wrapper to maintain API compatibility"""
    def __init__(self, template_state):
        self.template_state = template_state
        self._container = None
        self._page = None
    
    def build_for_page(self, page, on_change_callback=None):
        """Build the color picker for a specific page"""
        self._page = page
        self._container = create_color_picker(page, self.template_state, on_change_callback)
        return self._container
