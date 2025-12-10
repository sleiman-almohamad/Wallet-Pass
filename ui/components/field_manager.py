"""
Field Manager Component
Manage custom fields with add/remove/reorder functionality
Note: Flet doesn't have native drag-and-drop, so we use up/down buttons for reordering
"""

import flet as ft


class FieldManager(ft.UserControl):
    """
    Field manager for creating and managing custom pass fields
    Supports add, remove, and reorder operations
    """
    
    FIELD_TYPES = [
        {"value": "text", "label": "Text"},
        {"value": "number", "label": "Number"},
        {"value": "date", "label": "Date"},
        {"value": "datetime", "label": "Date/Time"},
        {"value": "email", "label": "Email"},
        {"value": "phone", "label": "Phone"}
    ]
    
    def __init__(self, template_state):
        super().__init__()
        self.template_state = template_state
        self.fields = template_state.get("fields", [])
    
    def build(self):
        """Build the field manager UI"""
        return ft.Container(
            content=ft.Column([
                # Header with add button
                ft.Row([
                    ft.Text("Custom Fields", size=16, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.icons.ADD_CIRCLE,
                        icon_color="blue",
                        tooltip="Add Field",
                        on_click=self._add_field
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Text(
                    "Define custom fields that will appear on the pass",
                    size=11,
                    color="grey"
                ),
                
                ft.Container(height=10),
                
                # Fields list
                ft.Column([
                    self._build_field_item(field, idx)
                    for idx, field in enumerate(self.fields)
                ], spacing=10) if self.fields else ft.Container(
                    content=ft.Text(
                        "No custom fields yet. Click + to add one.",
                        size=12,
                        color="grey",
                        italic=True
                    ),
                    padding=20,
                    bgcolor="grey100",
                    border_radius=8,
                    alignment=ft.alignment.center
                )
                
            ], spacing=10),
            padding=15,
            border=ft.border.all(1, "grey300"),
            border_radius=10
        )
    
    def _build_field_item(self, field, index):
        """Build a single field item with controls"""
        return ft.Container(
            content=ft.Column([
                # Field controls row
                ft.Row([
                    # Reorder buttons
                    ft.Column([
                        ft.IconButton(
                            icon=ft.icons.ARROW_UPWARD,
                            icon_size=16,
                            tooltip="Move Up",
                            on_click=lambda e, i=index: self._move_field(i, -1),
                            disabled=index == 0
                        ),
                        ft.IconButton(
                            icon=ft.icons.ARROW_DOWNWARD,
                            icon_size=16,
                            tooltip="Move Down",
                            on_click=lambda e, i=index: self._move_field(i, 1),
                            disabled=index == len(self.fields) - 1
                        )
                    ], spacing=0),
                    
                    # Field configuration
                    ft.Column([
                        ft.Row([
                            ft.TextField(
                                label="Field Name",
                                value=field.get("name", ""),
                                width=150,
                                on_change=lambda e, i=index: self._update_field(i, "name", e.control.value),
                                hint_text="e.g., seat_number"
                            ),
                            ft.TextField(
                                label="Label",
                                value=field.get("label", ""),
                                width=150,
                                on_change=lambda e, i=index: self._update_field(i, "label", e.control.value),
                                hint_text="e.g., Seat Number"
                            ),
                            ft.Dropdown(
                                label="Type",
                                value=field.get("type", "text"),
                                width=120,
                                options=[
                                    ft.dropdown.Option(ft["value"], ft["label"])
                                    for ft in self.FIELD_TYPES
                                ],
                                on_change=lambda e, i=index: self._update_field(i, "type", e.control.value)
                            )
                        ], spacing=10),
                        
                        ft.Row([
                            ft.TextField(
                                label="Hint Text (optional)",
                                value=field.get("hint", ""),
                                expand=True,
                                on_change=lambda e, i=index: self._update_field(i, "hint", e.control.value),
                                hint_text="e.g., Enter your seat number"
                            ),
                            ft.Checkbox(
                                label="Required",
                                value=field.get("required", False),
                                on_change=lambda e, i=index: self._update_field(i, "required", e.control.value)
                            )
                        ], spacing=10)
                    ], expand=True),
                    
                    # Delete button
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_color="red",
                        tooltip="Remove Field",
                        on_click=lambda e, i=index: self._remove_field(i)
                    )
                ], spacing=10)
            ]),
            bgcolor="grey50",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, "grey200")
        )
    
    def _add_field(self, e):
        """Add a new field"""
        new_field = {
            "id": f"field_{len(self.fields)}_{id(self)}",
            "name": f"field_{len(self.fields) + 1}",
            "label": f"Field {len(self.fields) + 1}",
            "type": "text",
            "hint": "",
            "required": False
        }
        self.fields.append(new_field)
        self.template_state.update("fields", self.fields)
        self.update()
    
    def _remove_field(self, index):
        """Remove a field"""
        if 0 <= index < len(self.fields):
            self.fields.pop(index)
            self.template_state.update("fields", self.fields)
            self.update()
    
    def _move_field(self, index, direction):
        """Move field up (-1) or down (+1)"""
        new_index = index + direction
        if 0 <= new_index < len(self.fields):
            # Swap fields
            self.fields[index], self.fields[new_index] = self.fields[new_index], self.fields[index]
            self.template_state.update("fields", self.fields)
            self.update()
    
    def _update_field(self, index, key, value):
        """Update a field property"""
        if 0 <= index < len(self.fields):
            self.fields[index][key] = value
            self.template_state.update("fields", self.fields)
            # Don't update UI on every keystroke to avoid lag
            # The state is updated, preview will reflect changes
