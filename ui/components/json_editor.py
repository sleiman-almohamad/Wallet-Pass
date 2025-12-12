"""
JSON Editor Component for displaying and editing JSON
"""

import flet as ft
import json
from typing import Dict, Any, Optional, Callable


class JSONEditor:
    """JSON preview/editor component with formatting and validation"""
    
    def __init__(self, initial_json: Dict[str, Any], 
                 on_change: Optional[Callable] = None,
                 read_only: bool = True):
        """
        Initialize JSON editor
        
        Args:
            initial_json: Initial JSON data
            on_change: Optional callback when JSON changes (receives parsed dict)
            read_only: Whether the editor is read-only
        """
        self.json_data = initial_json
        self.on_change = on_change
        self.read_only = read_only
        self.text_field = None
        self.error_text = None
    
    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format JSON with proper indentation"""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _on_text_change(self, e):
        """Handle text changes in editable mode"""
        if self.read_only:
            return
        
        try:
            # Try to parse JSON
            parsed = json.loads(e.control.value)
            self.json_data = parsed
            
            # Clear error
            if self.error_text:
                self.error_text.value = ""
                self.error_text.color = "green"
            
            # Trigger callback
            if self.on_change:
                self.on_change(parsed)
        
        except json.JSONDecodeError as ex:
            # Show error
            if self.error_text:
                self.error_text.value = f"Invalid JSON: {str(ex)}"
                self.error_text.color = "red"
    
    def update_json(self, new_json: Dict[str, Any]):
        """Update the JSON data and refresh display"""
        self.json_data = new_json
        if self.text_field:
            self.text_field.value = self._format_json(new_json)
    
    def build(self) -> ft.Container:
        """Build and return the JSON editor UI"""
        # Create text field for JSON
        self.text_field = ft.TextField(
            value=self._format_json(self.json_data),
            multiline=True,
            min_lines=15,
            max_lines=25,
            read_only=self.read_only,
            text_style=ft.TextStyle(
                font_family="Courier New",
                size=11
            ),
            border_color="grey400",
            focused_border_color="blue",
            on_change=self._on_text_change if not self.read_only else None
        )
        
        # Error/status text
        self.error_text = ft.Text(
            "",
            size=11,
            color="green"
        )
        
        # Copy button
        def copy_json(e):
            e.page.set_clipboard(self.text_field.value)
            self.error_text.value = "✓ Copied to clipboard!"
            self.error_text.color = "green"
            e.page.update()
        
        copy_button = ft.IconButton(
            icon="content_copy",
            tooltip="Copy JSON",
            on_click=copy_json
        )
        
        # Format button (if editable)
        def format_json(e):
            try:
                parsed = json.loads(self.text_field.value)
                self.text_field.value = self._format_json(parsed)
                self.error_text.value = "✓ Formatted"
                self.error_text.color = "green"
                e.page.update()
            except json.JSONDecodeError as ex:
                self.error_text.value = f"Cannot format: {str(ex)}"
                self.error_text.color = "red"
                e.page.update()
        
        format_button = ft.IconButton(
            icon="format_align_left",
            tooltip="Format JSON",
            on_click=format_json
        ) if not self.read_only else None
        
        # Build UI
        buttons = [copy_button]
        if format_button:
            buttons.append(format_button)
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("JSON Preview", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row(buttons, spacing=5)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=5),
                self.text_field,
                self.error_text
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, "grey300"),
            border_radius=5
        )
