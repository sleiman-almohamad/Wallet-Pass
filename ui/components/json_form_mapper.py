"""
JSON Form Mapper - Maps JSON structures to Flet form components
Handles nested JSON paths and generates dynamic forms
"""

import flet as ft
from typing import Dict, Any, Optional, Callable


def get_nested_value(data: Dict[str, Any], path: str) -> Optional[Any]:
    """
    Get value from nested dictionary using dot notation
    
    Args:
        data: The dictionary to search
        path: Dot-notation path (e.g., "programLogo.sourceUri.uri")
    
    Returns:
        The value at the path, or None if not found
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set value in nested dictionary using dot notation
    
    Args:
        data: The dictionary to modify
        path: Dot-notation path (e.g., "programLogo.sourceUri.uri")
        value: The value to set
    """
    keys = path.split('.')
    current = data
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the final value
    current[keys[-1]] = value


def create_form_field(field_path: str, field_metadata: Dict[str, str], 
                      current_value: Optional[str], 
                      on_change: Callable) -> ft.Control:
    """
    Create a Flet form field based on field metadata
    
    Args:
        field_path: JSON path for this field
        field_metadata: Metadata dict with 'label', 'type', 'hint'
        current_value: Current value for the field
        on_change: Callback function when value changes
    
    Returns:
        Flet control for the form field
    """
    field_type = field_metadata.get("type", "text")
    label = field_metadata.get("label", field_path)
    hint = field_metadata.get("hint", "")
    
    if field_type == "color":
        # Color field with hex input
        color_field = ft.TextField(
            label=label,
            hint_text=hint,
            value=current_value or "",
            width=300,
            prefix_text="#",
            max_length=6,
            on_change=lambda e: on_change(field_path, f"#{e.control.value}" if e.control.value and not e.control.value.startswith("#") else e.control.value)
        )
        # Remove # if already present in current_value
        if current_value and current_value.startswith("#"):
            color_field.value = current_value[1:]
        return color_field
    
    elif field_type == "url":
        # URL field with validation
        return ft.TextField(
            label=label,
            hint_text=hint,
            value=current_value or "",
            width=400,
            keyboard_type=ft.KeyboardType.URL,
            on_change=lambda e: on_change(field_path, e.control.value)
        )
    
    elif field_type == "datetime":
        # Datetime field
        return ft.TextField(
            label=label,
            hint_text=hint,
            value=current_value or "",
            width=300,
            on_change=lambda e: on_change(field_path, e.control.value)
        )
    
    elif field_type == "select":
        # Dropdown for select fields
        options = field_metadata.get("options", [])
        return ft.Dropdown(
            label=label,
            hint_text=hint,
            value=current_value or "",
            width=300,
            options=[ft.dropdown.Option(opt) for opt in options],
            on_change=lambda e: on_change(field_path, e.control.value)
        )
    
    else:  # text or default
        # Standard text field
        return ft.TextField(
            label=label,
            hint_text=hint,
            value=current_value or "",
            width=400,
            on_change=lambda e: on_change(field_path, e.control.value)
        )


def generate_dynamic_form(field_mappings: Dict[str, Dict[str, str]], 
                          json_data: Dict[str, Any],
                          on_field_change: Callable) -> list:
    """
    Generate a list of Flet form controls from field mappings
    
    Args:
        field_mappings: Dictionary mapping JSON paths to field metadata
        json_data: The current JSON data
        on_field_change: Callback when a field value changes (receives path and new value)
    
    Returns:
        List of Flet controls
    """
    form_controls = []
    
    for field_path, field_metadata in field_mappings.items():
        # Get current value from JSON
        current_value = get_nested_value(json_data, field_path)
        
        # Create the form field
        field = create_form_field(
            field_path, 
            field_metadata, 
            str(current_value) if current_value is not None else None,
            on_field_change
        )
        
        form_controls.append(field)
    
    return form_controls


class DynamicForm:
    """Container class for a dynamic form with state management"""
    
    def __init__(self, field_mappings: Dict[str, Dict[str, str]], 
                 initial_json: Dict[str, Any],
                 on_change_callback: Optional[Callable] = None):
        """
        Initialize dynamic form
        
        Args:
            field_mappings: Field definitions
            initial_json: Initial JSON data
            on_change_callback: Optional callback when form data changes
        """
        self.field_mappings = field_mappings
        self.json_data = initial_json.copy()
        self.on_change_callback = on_change_callback
        self.controls = []
    
    def _on_field_change(self, field_path: str, new_value: Any):
        """Handle field value changes"""
        # Update JSON data
        set_nested_value(self.json_data, field_path, new_value)
        
        # Trigger callback if provided
        if self.on_change_callback:
            self.on_change_callback(self.json_data)
    
    def build(self) -> list:
        """Build and return form controls"""
        self.controls = generate_dynamic_form(
            self.field_mappings,
            self.json_data,
            self._on_field_change
        )
        return self.controls
    
    def get_json_data(self) -> Dict[str, Any]:
        """Get current JSON data"""
        return self.json_data
    
    def update_json_data(self, new_json: Dict[str, Any]):
        """Update the entire JSON data and rebuild form"""
        self.json_data = new_json.copy()
        return self.build()
