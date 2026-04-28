import flet as ft
from ui.theme import BORDER_COLOR, SECTION_HEADER, TEXT_MUTED

class EmojiPicker:
    def __init__(self, page: ft.Page):
        self.page = page
        self.target_textfield = None
        self._build_dialog()

    def _build_dialog(self):
        import json
        import os
        
        emoji_path = os.path.join(os.path.dirname(__file__), "emoji_data.json")
        try:
            with open(emoji_path, "r", encoding="utf-8") as f:
                raw_cats = json.load(f)
             
            # Map Github gemoji categories to nicer Tab names
            name_map = {
                "Smileys & Emotion": "😀 Smileys",
                "People & Body": "👋 People",
                "Animals & Nature": "🐻 Nature",
                "Food & Drink": "🍔 Food",
                "Travel & Places": "🚗 Travel",
                "Activities": "🎪 Activities",
                "Objects": "🛠️ Objects",
                "Symbols": "🚩 Symbols",
                "Flags": "🏳️ Flags"
            }
            categories = {name_map.get(k, k): v for k, v in raw_cats.items()}
        except Exception:
            categories = {
                "😀 Smileys": ["😀", "😁", "😂", "🤣", "😊", "😇", "😍", "🥰", "😋", "😎", "🤔", "🙄", "😴", "🤐", "🥵"],
                "🎪 Activities": ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏓", "🏸", "🥊", "🥋", "🥅", "⛳", "⛸️"],
                "🛠️ Objects": ["💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "🗜️", "💽", "💾", "💿", "📀", "📼", "📷", "📸"],
                "🚩 Symbols": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗"]
            }

        tabs = []
        for name, emojis in categories.items():
            grid = ft.GridView(
                expand=1,
                runs_count=6,
                max_extent=45,
                child_aspect_ratio=1.0,
                spacing=5,
                run_spacing=5,
            )
            for e in emojis:
                grid.controls.append(
                    ft.TextButton(
                        text=e,
                        data=e,
                        on_click=self._on_emoji_click,
                        style=ft.ButtonStyle(padding=0, shape=ft.RoundedRectangleBorder(radius=4))
                    )
                )
            tabs.append(ft.Tab(tab_content=ft.Text(name, size=12), content=ft.Container(content=grid, padding=10)))

        self.tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=tabs,
            expand=1,
        )

        self.dialog = ft.AlertDialog(
            title=ft.Text("Select Emoji", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                height=300,
                content=self.tabs_control
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: self.close())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_emoji_click(self, e):
        emoji = e.control.data
        if self.target_textfield:
            self.target_textfield.value = (self.target_textfield.value or "") + emoji
            self.target_textfield.update()
            if hasattr(self.target_textfield, '_on_change_trigger') and self.target_textfield._on_change_trigger:
                self.target_textfield._on_change_trigger(None)

    def open(self, target_textfield, on_change_callback=None):
        self.target_textfield = target_textfield
        self.target_textfield._on_change_trigger = on_change_callback
        self.page.open(self.dialog)

    def close(self):
        self.page.close(self.dialog)

class AppleFieldEditor:
    """
    Dynamic Field Editor for Apple Wallet Passes.
    Supports primary (max 1), secondary (max 4), auxiliary (max 4), and back (unlimited) fields.
    Each field has a Label and a Value.
    """

    LIMITS = {
        "header": 2,
        "primary": 1,
        "secondary": 4,
        "auxiliary": 4,
        "back": float('inf'),
    }

    TITLES = {
        "header": "Header Fields",
        "primary": "Primary Field",
        "secondary": "Secondary Fields",
        "auxiliary": "Auxiliary Fields",
        "back": "Back Fields",
    }

    def __init__(self, page=None, on_change=None):
        self.page = page
        self.on_change = on_change
        self.emoji_picker = EmojiPicker(self.page) if self.page else None
        
        # Structure: dict of category -> list of Dicts {"label": TextField, "value": TextField, "row": ft.Row}
        self.fields = {
            "header": [],
            "primary": [],
            "secondary": [],
            "auxiliary": [],
            "back": [],
        }
        self.main_column = None

        # UI Containers for each section
        self.sections_ui = {
            "header": ft.Column(spacing=8),
            "primary": ft.Column(spacing=8),
            "secondary": ft.Column(spacing=8),
            "auxiliary": ft.Column(spacing=8),
            "back": ft.Column(spacing=8),
        }

    def build(self):
        main_column = ft.Column(spacing=15)
        
        for category in ["header", "primary", "secondary", "auxiliary", "back"]:
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
        if not col or not hasattr(col, "controls"): return
        
        for i, category in enumerate(["header", "primary", "secondary", "auxiliary", "back"]):
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
            on_change=on_text_change,
            suffix=ft.IconButton(
                icon=ft.Icons.EMOJI_EMOTIONS,
                icon_size=16,
                tooltip="Add Emoji",
                on_click=lambda e: self.emoji_picker.open(lbl_tf, on_text_change) if self.emoji_picker else None
            )
        )
        is_back = (category == "back")

        val_tf = ft.TextField(
            label="Value", 
            value=value_val, 
            hint_text=f"{self.TITLES[category]} Value",
            expand=1, border_radius=8, text_size=13,
            on_change=on_text_change,
            multiline=is_back,
            min_lines=3 if is_back else 1,
            max_lines=10 if is_back else 1,
            suffix=ft.IconButton(
                icon=ft.Icons.EMOJI_EMOTIONS,
                icon_size=16,
                tooltip="Add Emoji",
                on_click=lambda e: self.emoji_picker.open(val_tf, on_text_change) if self.emoji_picker else None
            )
        )

        remove_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="red400",
            tooltip="Remove Field"
        )
        
        row = ft.Row([lbl_tf, val_tf, remove_btn], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START if is_back else ft.CrossAxisAlignment.CENTER)

        
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
        for category in ["header", "primary", "secondary", "auxiliary", "back"]:
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

    def get_fields(self):
        """Alias for get_fields_data() for compatibility."""
        return self.get_fields_data()

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

    def load_fields(self, fields_list):
        """Alias for set_fields_data() for compatibility."""
        self.set_fields_data(fields_list)
        # Don't trigger change on initial load to avoid redundant triggers

    def reset(self):
        """Clear all dynamic fields and reset internal lists."""
        for cat in self.fields:
            self.fields[cat].clear()
            self.sections_ui[cat].controls.clear()
        self._update_add_buttons()
