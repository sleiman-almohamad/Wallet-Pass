"""
Text Module Row Editor 
A dynamic Flet component for managing multiple text module rows.
Supports Generic Pass textModulesData at the class and pass level.
"""

import flet as ft
from typing import List, Dict, Callable

class TextModuleRowEditor(ft.Container):
    def __init__(self, initial_rows: List[Dict] = None, on_change: Callable[[List[Dict]], None] = None, state=None, mode="class"):
        """
        initial_rows: list of dictionaries representing rows 
                     (class mode expects dicts with row_index, left_header, etc.)
                     (pass mode expects flat list of dicts with id, header, body)
        on_change: callback when the data changes
        mode: "class" (outputs TextModuleRowModel style) or "pass" (outputs flat TextModuleData style)
        """
        super().__init__()
        self.mode = mode
        self.state = state
        self.on_change_callback = on_change
        
        # Internal state always managed as "rows" of 3 columns
        self.rows = []
        if initial_rows:
            self.load_rows(initial_rows)
            
        # Call build logic to populate container content right away
        self.content = self._build_content()
        self.margin = ft.margin.only(top=10, bottom=10)

    def load_rows(self, initial_rows: List[Dict]):
        if self.mode == "class":
            self.rows = [dict(r) for r in initial_rows]
        else:
            # Pass mode: recreate rows from flat list of modules
            row_dict = {}
            for mod in initial_rows:
                mod_id = mod.get('id', '')
                header = mod.get('header', '')
                body = mod.get('body', '')
                m_type = mod.get('module_type', mod.get('type', 'text'))
                
                parts = mod_id.split('_')
                if len(parts) >= 3 and parts[0] == 'row':
                    try:
                        r_idx = int(parts[1])
                        col = parts[2]
                        
                        if r_idx not in row_dict:
                            row_dict[r_idx] = {'row_index': r_idx}
                        
                        if col in ['left', 'middle', 'right']:
                            row_dict[r_idx][f'{col}_header'] = header
                            row_dict[r_idx][f'{col}_body'] = body
                            row_dict[r_idx][f'{col}_type'] = m_type
                    except ValueError:
                        pass
            
            self.rows = [row_dict[k] for k in sorted(row_dict.keys())]

    def _trigger_change(self):
        if not self.on_change_callback:
            return
            
        if self.mode == "class":
            self.on_change_callback(self.rows)
        else:
            # Flatten to pass mode
            flat_modules = []
            for r_idx, row in enumerate(self.rows):
                # Left
                l_hdr = row.get('left_header')
                l_bdy = row.get('left_body')
                l_typ = row.get('left_type', 'text')
                if l_hdr or l_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_left', 'header': l_hdr or '', 'body': l_bdy or '', 'module_type': l_typ})
                
                # Middle
                m_hdr = row.get('middle_header')
                m_bdy = row.get('middle_body')
                m_typ = row.get('middle_type', 'text')
                if m_hdr or m_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_middle', 'header': m_hdr or '', 'body': m_bdy or '', 'module_type': m_typ})
                
                # Right
                r_hdr = row.get('right_header')
                r_bdy = row.get('right_body')
                r_typ = row.get('right_type', 'text')
                if r_hdr or r_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_right', 'header': r_hdr or '', 'body': r_bdy or '', 'module_type': r_typ})
                    
            self.on_change_callback(flat_modules)

    def get_rows(self) -> List[Dict]:
        """Return the current rows formatted according to the current mode."""
        if self.mode == "class":
            return self.rows
        else:
            # Flatten to pass mode
            flat_modules = []
            for r_idx, row in enumerate(self.rows):
                # Left
                l_hdr = row.get('left_header')
                l_bdy = row.get('left_body')
                l_typ = row.get('left_type', 'text')
                if l_hdr or l_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_left', 'header': l_hdr or '', 'body': l_bdy or '', 'module_type': l_typ})
                
                # Middle
                m_hdr = row.get('middle_header')
                m_bdy = row.get('middle_body')
                m_typ = row.get('middle_type', 'text')
                if m_hdr or m_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_middle', 'header': m_hdr or '', 'body': m_bdy or '', 'module_type': m_typ})
                
                # Right
                r_hdr = row.get('right_header')
                r_bdy = row.get('right_body')
                r_typ = row.get('right_type', 'text')
                if r_hdr or r_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_right', 'header': r_hdr or '', 'body': r_bdy or '', 'module_type': r_typ})
                    
            return flat_modules

    def remove_row(self, index: int):
        if 0 <= index < len(self.rows):
            self.rows.pop(index)
            # Reassign row indices
            for i, r in enumerate(self.rows):
                r['row_index'] = i
            self.content = self._build_content()
            self.update()
            self._trigger_change()

    def update_field(self, row_idx: int, field: str, value: str):
        if 0 <= row_idx < len(self.rows):
            self.rows[row_idx][field] = value
            if field.endswith('_type'):
                # Refresh UI to update labels if type changed
                self.content = self._build_content()
                self.update()
            self._trigger_change()

    def build_row_ui(self, row_data: Dict, index: int):
        def make_field(col_prefix, label_postfix):
            field_name = f"{col_prefix}_{label_postfix.lower()}"
            current_type = row_data.get(f"{col_prefix}_type", "text")
            
            # Map labels based on type
            display_label = label_postfix
            if current_type == "link":
                if label_postfix == "Header": display_label = "Button Label"
                if label_postfix == "Body":   display_label = "Target URL"

            label = f"{col_prefix.capitalize()} {display_label}"
            
            return ft.TextField(
                label=label,
                value=row_data.get(field_name, ""),
                width=160 if self.mode == "class" else 120,
                text_size=11,
                height=45,
                content_padding=5,
                on_change=lambda e: self.update_field(index, field_name, e.control.value)
            )

        def build_col(prefix):
            col_type = row_data.get(f"{prefix}_type", "text")
            type_picker = ft.Dropdown(
                value=col_type,
                options=[
                    ft.dropdown.Option("text", "Text"),
                    ft.dropdown.Option("link", "Link"),
                ],
                width=80 if self.mode == "class" else 70,
                text_size=10,
                content_padding=5,
                on_change=lambda e: self.update_field(index, f"{prefix}_type", e.control.value)
            )
            
            if self.mode == "class":
                # In class mode, we usually only define the header (blueprint)
                return ft.Column([
                    ft.Row([ft.Text(prefix.upper(), size=9, weight="bold"), type_picker], spacing=5),
                    make_field(prefix, "Header")
                ], spacing=5)
            else:
                # In pass mode, we provide values for header and body
                return ft.Column([
                    ft.Row([ft.Text(prefix.upper(), size=9, weight="bold"), type_picker], spacing=5),
                    make_field(prefix, "Header"),
                    make_field(prefix, "Body")
                ], spacing=3)

        return ft.Container(
            border=ft.border.all(1, "grey300"),
            border_radius=8,
            padding=10,
            margin=ft.margin.only(bottom=10),
            bgcolor="white",
            content=ft.Column([
                ft.Row([
                    ft.Text(f"ROW {index + 1}", weight=ft.FontWeight.W_600, size=12),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color="red400",
                        icon_size=18,
                        on_click=lambda e, i=index: self.remove_row(i)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    build_col("left"),
                    build_col("middle"),
                    build_col("right"),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
            ])
        )

    def _build_content(self):
        rows_list = ft.Column(
            controls=[self.build_row_ui(row_data, i) for i, row_data in enumerate(self.rows)],
            spacing=5
        )

        return ft.Column([
            ft.Row([
                ft.Text("Information Fields", size=14, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Add Row", icon=ft.Icons.ADD, on_click=self.add_row, 
                                 style=ft.ButtonStyle(padding=5, shape=ft.RoundedRectangleBorder(radius=8))),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text("Define text blocks or interactive link buttons.", size=11, color="grey"),
            ft.Container(height=5),
            rows_list
        ])

    def add_row(self, e):
        new_index = len(self.rows)
        self.rows.append({
            'row_index': new_index,
            'left_type': 'text', 'middle_type': 'text', 'right_type': 'text'
        })
        self.content = self._build_content()
        self.update()
        self._trigger_change()
