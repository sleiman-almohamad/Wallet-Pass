import flet as ft
from ui.theme import BORDER_COLOR, SECTION_HEADER, TEXT_MUTED

class AppleFieldEditor:
    """
    Dynamic Field Editor for Apple Wallet Passes.
    Supports primary (max 1), secondary (max 4), auxiliary (max 4), and back (unlimited) fields.
    Each field has a Label and a Value.
    """

    LIMITS = {
        "primary": 1,
        "secondary": 4,
        "auxiliary": 4,
        "back": float('inf'),
    }

    TITLES = {
        "primary": "Primary Field",
        "secondary": "Secondary Fields",
        "auxiliary": "Auxiliary Fields",
        "back": "Back Fields",
    }

    def __init__(self, on_change=None):
        self.on_change = on_change
        
        # Structure: dict of category -> list of Dicts {"label": TextField, "value": TextField, "row": ft.Row}
        self.fields = {
            "primary": [],
            "secondary": [],
            "auxiliary": [],
            "back": [],
        }

        # UI Containers for each section
        self.sections_ui = {
            "primary": ft.Column(spacing=8),
            "secondary": ft.Column(spacing=8),
            "auxiliary": ft.Column(spacing=8),
            "back": ft.Column(spacing=8),
        }

    def build(self):
        main_column = ft.Column(spacing=15)
        
        for category in ["primary", "secondary", "auxiliary", "back"]:
            title_text = ft.Text(self.TITLES[category], size=12, weight=ft.FontWeight.W_600, color=SECTION_HEADER)
            
            add_button = ft.TextButton(
                "Add Field",
                icon=ft.Icons.ADD,
                on_click=lambda e, cat=category: self._add_field(cat),
                style=ft.ButtonStyle(color="blue")
            )
            
            # Store button ref in the category dict if needed, or update dynamically
            # Here we just wrap them in a Column
            cat_container = ft.Column([
                ft.Row([title_text, add_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.sections_ui[category],
                ft.Divider(height=1, color=BORDER_COLOR)
            ], spacing=5)
            
            main_column.controls.append(cat_container)

        self._update_add_buttons(main_column)
        self.main_column = main_column
        return self.main_column

    def _trigger_change(self):
        if self.on_change:
            self.on_change()

    def _update_add_buttons(self, main_column=None):
        col = main_column or self.main_column
        if not col: return
        
        for i, category in enumerate(["primary", "secondary", "auxiliary", "back"]):
            # Each cat_container is at index `i` in main_column
            cat_container = col.controls[i]
            row_header = cat_container.controls[0]
            add_button = row_header.controls[1]
            
            current_count = len(self.fields[category])
            limit = self.LIMITS[category]
            
            add_button.disabled = current_count >= limit
            
        if hasattr(self, 'main_column') and self.main_column and self.main_column.page:
            self.main_column.update()

    def _add_field(self, category, label_val="", value_val=""):
        if len(self.fields[category]) >= self.LIMITS[category]:
            return

        def on_text_change(e):
            self._trigger_change()

        lbl_tf = ft.TextField(
            label="Label", 
            value=label_val, 
            hint_text=f"{self.TITLES[category]} Label",
            expand=1, border_radius=8, text_size=13,
            on_change=on_text_change
        )
        val_tf = ft.TextField(
            label="Value", 
            value=value_val, 
            hint_text=f"{self.TITLES[category]} Value",
            expand=1, border_radius=8, text_size=13,
            on_change=on_text_change
        )

        remove_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="red400",
            tooltip="Remove Field"
        )
        
        row = ft.Row([lbl_tf, val_tf, remove_btn], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        field_obj = {
            "label_tf": lbl_tf,
            "value_tf": val_tf,
            "row": row
        }
        
        def remove_row(e, f_obj=field_obj, cat=category):
            self.fields[cat].remove(f_obj)
            self.sections_ui[cat].controls.remove(f_obj["row"])
            self._update_add_buttons()
            self._trigger_change()

        remove_btn.on_click = remove_row

        self.fields[category].append(field_obj)
        self.sections_ui[category].controls.append(row)
        
        self._update_add_buttons()
        self._trigger_change()

    def get_fields_data(self):
        """Returns a list of dicts: [{'field_type': str, 'label': str, 'value': str}]"""
        result = []
        for category in ["primary", "secondary", "auxiliary", "back"]:
            for field in self.fields[category]:
                lbl = field["label_tf"].value
                val = field["value_tf"].value
                if lbl or val:  # Only add if at least one is not empty
                    result.append({
                        "field_type": category,
                        "label": lbl or "",
                        "value": val or ""
                    })
        return result

    def set_fields_data(self, fields_list):
        """Populates the UI from a list of dicts."""
        # Clear existing
        for cat in self.fields:
            self.fields[cat].clear()
            self.sections_ui[cat].controls.clear()
            
        if not fields_list:
            # Initialize with one empty row for each category for better UX (or just let user click Add)
            pass
        else:
            for field in fields_list:
                cat = field.get("field_type")
                if cat in self.fields:
                    self._add_field(cat, field.get("label", ""), field.get("value", ""))
                    
        self._update_add_buttons()
        # Don't trigger change on initial load to avoid redundant triggers
