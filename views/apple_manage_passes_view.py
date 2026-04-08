import flet as ft
from ui.components.color_picker import create_color_picker
from ui.components.mobile_mockup import MobileMockupPreview
from ui.components.apple_field_editor import AppleFieldEditor

def build_apple_manage_passes_view(page: ft.Page, state, api_client, preview: MobileMockupPreview):
    """
    Build the Manage Passes tab content for Apple Wallet.
    """
    # ── State ──
    pass_data = {}
    
    # ── Refs for form fields ──
    holder_name_ref = ft.Ref[ft.TextField]()
    holder_email_ref = ft.Ref[ft.TextField]()
    org_name_ref = ft.Ref[ft.TextField]()
    logo_text_ref = ft.Ref[ft.TextField]()
    logo_url_ref = ft.Ref[ft.TextField]()
    strip_url_ref = ft.Ref[ft.TextField]()
    # ── Apple Field Editor ──
    # Added later, so we initialize below where on_form_change is defined

    class SimpleColorState:
        def __init__(self, initial_state, on_change_callback):
            self.state = initial_state
            self.on_change = on_change_callback
        def get(self, key, default=None):
            return self.state.get(key, default)
        def update(self, key, value):
            self.state[key] = value
            if self.on_change:
                self.on_change()

    custom_color_state = {
        "background_color": "#1a1a2e",
        "foreground_color": "#ffffff",
        "label_color": "#bbbbbb"
    }
    
    bg_color_picker_container = ft.Container(content=None)
    fg_color_picker_container = ft.Container(content=None)
    lbl_color_picker_container = ft.Container(content=None)

    def on_form_change(e=None):
        if holder_name_ref.current:
            pass_data["holder_name"] = holder_name_ref.current.value
        if holder_email_ref.current:
            pass_data["holder_email"] = holder_email_ref.current.value
        if org_name_ref.current:
            pass_data["org_name"] = org_name_ref.current.value
        if logo_text_ref.current:
            pass_data["logo_text"] = logo_text_ref.current.value
        if logo_url_ref.current:
            pass_data["logo_url"] = logo_url_ref.current.value
        if strip_url_ref.current:
            pass_data["strip_url"] = strip_url_ref.current.value
            
        pass_data["dynamic_fields"] = apple_field_editor.get_fields_data()
            
        pass_data["bg_color"] = custom_color_state.get("background_color")
        pass_data["fg_color"] = custom_color_state.get("foreground_color")
        pass_data["label_color"] = custom_color_state.get("label_color")
        
        preview.update_data(pass_data, "apple")

    apple_field_editor = AppleFieldEditor(on_change=on_form_change)
    color_state_obj = SimpleColorState(custom_color_state, on_form_change)
    bg_color_picker_container.content = create_color_picker(page, color_state_obj, on_form_change, "background_color", "Background Color")
    fg_color_picker_container.content = create_color_picker(page, color_state_obj, on_form_change, "foreground_color", "Foreground Color")
    lbl_color_picker_container.content = create_color_picker(page, color_state_obj, on_form_change, "label_color", "Label Color")
    
    # ── UI Controls ──
    template_dropdown = ft.Dropdown(
        label="Select Template",
        hint_text="Loading templates...",
        width=380, border_radius=8, text_size=13,
        options=[]
    )

    pass_dropdown = ft.Dropdown(
        label="Select Pass",
        hint_text="Choose a pass...",
        width=380, border_radius=8, text_size=13,
        options=[],
        visible=False
    )
    
    edit_form = ft.Column(visible=False, spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    def load_templates():
        try:
            templates = api_client.get_apple_templates() if hasattr(api_client, "get_apple_templates") else []
            if templates:
                template_dropdown.options = [
                    ft.dropdown.Option(str(t["template_id"]), f"{t.get('template_name', 'Unnamed')} ({t.get('pass_style', 'unknown')})")
                    for t in templates
                ]
                template_dropdown.hint_text = "Choose a template..."
            else:
                template_dropdown.options = []
                template_dropdown.hint_text = "No Apple templates found."
        except Exception as e:
            print(f"Error loading Apple templates: {e}")
            template_dropdown.options = []
            template_dropdown.hint_text = "Error loading templates."
        if template_dropdown.page:
            template_dropdown.update()

    def load_passes_for_template(template_id: str):
        try:
            if hasattr(api_client, "get_all_apple_passes"):
                all_passes = api_client.get_all_apple_passes()
            else:
                all_passes = []
            
            # Filter passes by template_id
            template_passes = [p for p in all_passes if str(p.get("template_id", "")) == template_id]
            
            if template_passes:
                pass_dropdown.options = [
                    ft.dropdown.Option(
                        str(p.get("serial_number", "")),
                        p.get("holder_name", "Unknown")
                    )
                    for p in template_passes
                ]
                pass_dropdown.hint_text = f"Found {len(template_passes)} passes. Select one."
            else:
                pass_dropdown.options = []
                pass_dropdown.hint_text = "No passes found for this template."
        except Exception as e:
            print(f"Error loading Apple passes: {e}")
            pass_dropdown.options = []
            pass_dropdown.hint_text = "Error loading passes."
        
        pass_dropdown.value = None
        if pass_dropdown.page:
            pass_dropdown.update()

    # Load templates immediately on initialization
    load_templates()
    if state and hasattr(state, "register_refresh_callback"):
        state.register_refresh_callback("apple_manage_passes_templates", load_templates)

    def on_template_change(e):
        if template_dropdown.value:
            pass_dropdown.visible = True
            load_passes_for_template(template_dropdown.value)
            edit_form.visible = False
        else:
            pass_dropdown.visible = False
            edit_form.visible = False
        page.update()

    def on_pass_change(e):
        if pass_dropdown.value:
            try:
                serial_number = pass_dropdown.value
                p_data = api_client.get_apple_pass(serial_number) if hasattr(api_client, "get_apple_pass") else {}
                
                if not p_data:
                    return

                edit_form.visible = True
                
                holder_name_ref.current.value = p_data.get("holder_name", "")
                holder_email_ref.current.value = p_data.get("holder_email", "")
                
                custom_color_state["background_color"] = p_data.get("background_color", "#1a1a2e")
                custom_color_state["foreground_color"] = p_data.get("foreground_color", "#ffffff")
                custom_color_state["label_color"] = p_data.get("label_color", "#bbbbbb")
                
                org_name_ref.current.value = p_data.get("organization_name", "")
                logo_text_ref.current.value = p_data.get("logo_text", "")
                logo_url_ref.current.value = p_data.get("logo_url", "")
                strip_url_ref.current.value = p_data.get("strip_url", "")
                
                
                def _get_fields(src_list, t_name):
                    res = []
                    for f in src_list:
                        res.append({
                            "field_type": t_name,
                            "label": f.get("label", ""),
                            "value": f.get("value", "")
                        })
                    return res

                # Check where backend returns the fields list today. Often in pass_data.
                # If they are separate arrays (primary_fields, etc.) we combine them:
                loaded_fields = []
                loaded_fields.extend(_get_fields(p_data.get("primary_fields", []), "primary"))
                loaded_fields.extend(_get_fields(p_data.get("secondary_fields", []), "secondary"))
                loaded_fields.extend(_get_fields(p_data.get("auxiliary_fields", []), "auxiliary"))
                loaded_fields.extend(_get_fields(p_data.get("back_fields", []), "back"))
                
                # Check pass_data wrapper just in case
                if not loaded_fields and "pass_data" in p_data:
                    c_pd = p_data["pass_data"]
                    loaded_fields.extend(_get_fields(c_pd.get("primary_fields", []), "primary"))
                    loaded_fields.extend(_get_fields(c_pd.get("secondary_fields", []), "secondary"))
                    loaded_fields.extend(_get_fields(c_pd.get("auxiliary_fields", []), "auxiliary"))
                    loaded_fields.extend(_get_fields(c_pd.get("back_fields", []), "back"))
                    
                    # Alternatively, if dynamic_fields list was stored directly:
                    if "dynamic_fields" in c_pd:
                        loaded_fields.extend(c_pd["dynamic_fields"])

                # Remove duplicates just in case
                unique_fields = []
                _seen = set()
                for lf in loaded_fields:
                    sig = (lf["field_type"], lf["label"], lf["value"])
                    if sig not in _seen:
                        _seen.add(sig)
                        unique_fields.append(lf)

                apple_field_editor.set_fields_data(unique_fields)
                
                on_form_change()
            except Exception as exc:
                print(f"Error loading Apple pass data: {exc}")
        page.update()

    template_dropdown.on_change = on_template_change
    pass_dropdown.on_change = on_pass_change

    def save_pass(e):
        try:
            serial_number = pass_dropdown.value
            if not serial_number: return
            
            update_payload = {
                "holder_name": pass_data.get("holder_name"),
                "holder_email": pass_data.get("holder_email"),
                "organization_name": pass_data.get("org_name"),
                "logo_text": pass_data.get("logo_text"),
                "logo_url": pass_data.get("logo_url"),
                "strip_url": pass_data.get("strip_url"),
                "background_color": custom_color_state.get("background_color"),
                "foreground_color": custom_color_state.get("foreground_color"),
                "label_color": custom_color_state.get("label_color"),
            }
            
            dynamic_fields = apple_field_editor.get_fields_data()
            def _extract_fields(ftype):
                return [{"key": f"{ftype}_{i}", "label": f["label"], "value": f["value"]}
                        for i, f in enumerate(dynamic_fields) if f["field_type"] == ftype]

            update_payload["primary_fields"] = _extract_fields("primary")
            update_payload["secondary_fields"] = _extract_fields("secondary")
            update_payload["auxiliary_fields"] = _extract_fields("auxiliary")
            update_payload["back_fields"] = _extract_fields("back")
            update_payload["dynamic_fields"] = dynamic_fields

            # Clean payload
            update_payload = {k: v for k, v in update_payload.items() if v is not None}
            
            if hasattr(api_client, "update_apple_pass"):
                api_client.update_apple_pass(serial_number, **update_payload)
                
                # --- Success Dialog ---
                def close_dlg(e):
                    page.close(upd_dlg)

                upd_dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("✅ Pass Updated Successfully!", weight=ft.FontWeight.BOLD),
                    content=ft.Text(f"Pass {serial_number} has been updated successfully.", size=13),
                    actions=[
                        ft.TextButton("Close", on_click=close_dlg),
                    ],
                )
                page.open(upd_dlg)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ update_apple_pass not implemented in client"))
                page.snack_bar.open = True
                
        except Exception as exc:
            print(f"Error saving Apple pass: {exc}")
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error: {exc}"))
            page.snack_bar.open = True
        
        page.update()

    save_btn = ft.ElevatedButton(
        "Save Pass Updates",
        icon=ft.Icons.SAVE,
        on_click=save_pass,
        bgcolor="#1a1a2e", color="white"
    )

    # Build internal form structure
    edit_form.controls = [
        ft.Text("Edit Pass Details", size=18, weight=ft.FontWeight.BOLD),
        ft.TextField(ref=holder_name_ref, label="Holder Name", on_change=on_form_change),
        ft.TextField(ref=holder_email_ref, label="Holder Email", on_change=on_form_change),
        ft.Divider(),
        
        ft.Text("Visual Branding", size=18, weight=ft.FontWeight.BOLD),
        ft.Row([
            bg_color_picker_container,
            fg_color_picker_container,
            lbl_color_picker_container,
        ], spacing=15, scroll=ft.ScrollMode.AUTO),
        ft.TextField(ref=org_name_ref, label="Organization Name", on_change=on_form_change),
        ft.TextField(ref=logo_text_ref, label="Logo Text", on_change=on_form_change),
        ft.TextField(ref=logo_url_ref, label="Logo URL", on_change=on_form_change),
        ft.TextField(ref=strip_url_ref, label="Strip Image URL", on_change=on_form_change),
        ft.Divider(),
        
        ft.Text("Card Fields", size=18, weight=ft.FontWeight.BOLD),
        apple_field_editor.build(),
        
        ft.Container(height=10),
        save_btn,
        ft.Container(height=20)
    ]

    left_panel = ft.Container(
        expand=1,
        padding=20,
        content=ft.Column([
            ft.Text("Manage Apple Passes", size=22, weight=ft.FontWeight.BOLD),
            template_dropdown,
            pass_dropdown,
            edit_form
        ], scroll=ft.ScrollMode.AUTO, expand=True)
    )
    
    # Initialize the preview to apple mode empty 
    preview.update_data({"bg_color": "#1a1a2e"}, "apple")
    
    return left_panel
