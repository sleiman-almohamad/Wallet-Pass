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
            # Modules typically have id like "row_0_left" or similar.
            row_dict = {}
            for mod in initial_rows:
                mod_id = mod.get('id', '')
                header = mod.get('header', '')
                body = mod.get('body', '')
                
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
                # We enforce row_index to match current position in flat output
                # Left
                l_hdr = row.get('left_header')
                l_bdy = row.get('left_body')
                if l_hdr or l_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_left', 'header': l_hdr or '', 'body': l_bdy or ''})
                
                # Middle
                m_hdr = row.get('middle_header')
                m_bdy = row.get('middle_body')
                if m_hdr or m_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_middle', 'header': m_hdr or '', 'body': m_bdy or ''})
                
                # Right
                r_hdr = row.get('right_header')
                r_bdy = row.get('right_body')
                if r_hdr or r_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_right', 'header': r_hdr or '', 'body': r_bdy or ''})
                    
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
                if l_hdr or l_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_left', 'header': l_hdr or '', 'body': l_bdy or ''})
                
                # Middle
                m_hdr = row.get('middle_header')
                m_bdy = row.get('middle_body')
                if m_hdr or m_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_middle', 'header': m_hdr or '', 'body': m_bdy or ''})
                
                # Right
                r_hdr = row.get('right_header')
                r_bdy = row.get('right_body')
                if r_hdr or r_bdy:
                    flat_modules.append({'id': f'row_{r_idx}_right', 'header': r_hdr or '', 'body': r_bdy or ''})
                    
            return flat_modules

    def add_row(self, e):
        new_index = len(self.rows)
        self.rows.append({'row_index': new_index})
        self.update()
        self._trigger_change()

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
            self._trigger_change()

    def build_row_ui(self, row_data: Dict, index: int):
        def make_field(col_prefix, label_postfix):
            field_name = f"{col_prefix}_{label_postfix.lower()}"
            label_key = f"label.{col_prefix}"
            postfix_key = f"label.{label_postfix.lower()}"
            label = f"{self.state.t(label_key)} {self.state.t(postfix_key)}" if self.state else f"{col_prefix.capitalize()} {label_postfix}"
            
            return ft.TextField(
                label=label,
                value=row_data.get(field_name, ""),
                width=120,
                text_size=12,
                height=45,
                content_padding=5,
                on_change=lambda e: self.update_field(index, field_name, e.control.value)
            )

        return ft.Container(
            border=ft.border.all(1, "grey300"),
            border_radius=5,
            padding=10,
            margin=ft.margin.only(bottom=10),
            bgcolor="grey50",
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{self.state.t('label.row') if self.state else 'Row'} {index + 1}", weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon="delete",
                        icon_color="red",
                        tooltip=self.state.t("tooltip.remove_row") if self.state else "Remove Row",
                        on_click=lambda e, i=index: self.remove_row(i)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Column([make_field("left", "Header"), make_field("left", "Body")], spacing=5),
                    ft.Column([make_field("middle", "Header"), make_field("middle", "Body")], spacing=5),
                    ft.Column([make_field("right", "Header"), make_field("right", "Body")], spacing=5),
                ], spacing=10)
            ])
        )

    def _build_content(self):
        rows_list = ft.Column(
            controls=[self.build_row_ui(row_data, i) for i, row_data in enumerate(self.rows)],
            spacing=5
        )

        return ft.Column([
            ft.Row([
                ft.Text(self.state.t("label.text_module_rows") if self.state else "Text Module Rows", size=14, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(self.state.t("btn.add_row") if self.state else "Add Row", icon="add", on_click=self.add_row, style=ft.ButtonStyle(padding=5)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(self.state.t("msg.row_hint") if self.state else "Supports up to 3 columns per row on the pass.", size=10, color="grey"),
            rows_list
        ])

    def add_row(self, e):
        new_index = len(self.rows)
        self.rows.append({'row_index': new_index})
        self.content = self._build_content()
        self.update()
        self._trigger_change()
