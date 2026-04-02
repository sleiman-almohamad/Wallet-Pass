"""
Apple Manage Passes View
Extracted from monolithic manage_passes_view.py — 3-panel layout for managing individual Apple Wallet pass objects.
"""

import flet as ft
from ui.components.json_editor import JSONEditor
from ui.components.color_picker import create_color_picker
from ui.components.mobile_mockup import MobileMockupPreview
import configs

def build_apple_manage_passes_view(page: ft.Page, state, api_client, preview: MobileMockupPreview) -> ft.Container:
    """
    Build the Manage Passes tab content for Apple Wallet.
    """
    ps = state.pass_state  # shorthand

    # ── Local mutable refs (UI-only) ──
    passes_current_json = {}
    apple_edit_refs = {} # For formatting Apple fields natively

    # ── UI Controls ──
    action_button_ref = ft.Ref[ft.ElevatedButton]()

    manage_passes_class_dropdown = ft.Dropdown(
        hint_text=state.t("label.select_template"),
        width=400,
        options=[],
        label=None
    )

    manage_passes_dropdown = ft.Dropdown(
        hint_text=state.t("label.select_pass"),
        width=400,
        options=[],
        label=None
    )

    passes_status = ft.Text("", size=12)

    passes_object_id_field = ft.TextField(
        hint_text=state.t("label.object_id"), width=400, read_only=True, bgcolor="grey100", label=None
    )
    passes_class_id_field = ft.TextField(
        hint_text=state.t("label.class_id"), width=400, read_only=True, bgcolor="grey100", label=None
    )

    passes_form_container = ft.Column(
        controls=[ft.Text(state.t("msg.load_template_hint"), color="grey", size=11)],
        spacing=8,
        scroll="auto",
    )
    passes_result_container = ft.Container(content=None)

    # ── Helpers ──

    def _set_status(msg, color="green"):
        passes_status.value = msg
        passes_status.color = color

    # ── Business-logic handlers ──

    def load_passes_classes():
        """Load classes into the Manage Passes class dropdown."""
        try:
            classes = api_client.get_classes() if api_client else []
            current_val = manage_passes_class_dropdown.value
            
            if classes and len(classes) > 0:
                manage_passes_class_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(cls.get("class_id", "")), 
                        text=f"{str(cls.get('class_id', '')).split('.')[-1]} ({cls.get('class_type', 'Unknown')})"
                    )
                    for cls in classes if cls.get("class_id")
                ]
                
                if current_val and any(str(c.get("class_id", "")) == current_val for c in classes):
                    manage_passes_class_dropdown.value = current_val
                else:
                    manage_passes_class_dropdown.value = None
                    manage_passes_class_dropdown.hint_text = state.t("label.select_template")
                
                _set_status(state.t("msg.loaded_classes", count=len(classes)))
            else:
                manage_passes_class_dropdown.options = []
                manage_passes_class_dropdown.value = None
                manage_passes_class_dropdown.hint_text = state.t("msg.no_templates")
                _set_status(state.t("msg.no_templates"), "blue")
            
            if not manage_passes_class_dropdown.value:
                manage_passes_dropdown.options = []
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = "Select a class first"
            
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading classes: {e}", "red")
            page.update()

    def refresh_manage_passes():
        load_passes_classes()
        if manage_passes_class_dropdown.value:
            load_passes_for_class(manage_passes_class_dropdown.value)

    state.register_refresh_callback("manage_passes_list", refresh_manage_passes)

    def load_passes_for_class(class_id: str):
        """Load Apple passes for a specific class from local database."""
        _set_status("⏳ Fetching passes from local database...", "blue")
        page.update()
        try:
            if hasattr(api_client, "get_all_apple_passes"):
                all_apple_passes = api_client.get_all_apple_passes()
            else:
                all_apple_passes = []
            
            passes = [p for p in all_apple_passes if str(p.get("class_id", "")) == class_id]
            for p in passes:
                p["object_id"] = p.get("serial_number") # Map for dropdown usage

            if passes and len(passes) > 0:
                manage_passes_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(p.get("object_id", "")),
                        text=p.get("holder_name", "Unknown")
                    )
                    for p in passes if p.get("object_id")
                ]
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = state.t("label.select_pass")
                _set_status(state.t("msg.found_passes", count=len(passes)))
            else:
                manage_passes_dropdown.options = []
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = state.t("msg.no_passes_found")
                _set_status(state.t("msg.no_passes_found"), "blue")
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading passes: {e}", "red")
            page.update()

    def on_passes_class_change(e):
        selected_class = manage_passes_class_dropdown.value
        if selected_class:
            load_passes_for_class(selected_class)
        else:
            manage_passes_dropdown.options = []
            manage_passes_dropdown.value = None
            manage_passes_dropdown.hint_text = "Select a class first"
            page.update()

    manage_passes_class_dropdown.on_change = on_passes_class_change

    def show_pass(e):
        nonlocal passes_current_json

        if not manage_passes_dropdown.value:
            _set_status(state.t("msg.select_pass_err"), "red"); page.update(); return

        _set_status(state.t("msg.saving_local"), "blue"); page.update()

        try:
            object_id = manage_passes_dropdown.value
            
            p_data = api_client.get_apple_pass(object_id) if hasattr(api_client, "get_apple_pass") else None
            if not p_data:
                _set_status(state.t("msg.template_not_found", id=object_id), "red"); page.update(); return
            
            passes_object_id_field.value = str(object_id).split('.')[-1]
            passes_object_id_field.data = object_id
            class_id_raw = str(p_data.get("class_id",""))
            passes_class_id_field.value = class_id_raw.split('.')[-1]
            passes_class_id_field.data = class_id_raw

            class_info = api_client.get_class(p_data.get("class_id"))

            passes_current_json = p_data.copy()
            passes_form_container.controls.clear()
            apple_edit_refs.clear()

            def _apple_field(name, label, hint, initial):
                r = ft.Ref[ft.TextField]()
                apple_edit_refs[name] = r
                return ft.TextField(
                    ref=r, label=label, hint_text=hint, value=initial or "",
                    width=380, expand=True,
                    on_change=lambda e: update_apple_preview()
                )

            def _apple_pair(name_prefix, visuals_key, container):
                header = "Primary" if "primary" in visuals_key else "Secondary" if "secondary" in visuals_key else "Auxiliary" if "auxiliary" in visuals_key else "Back" if "back" in visuals_key else "Top Row"
                fields = p_data.get("visual_data", {}).get(visuals_key, [])
                first_field = fields[0] if fields and len(fields)>0 else {}
                
                lbl_field = _apple_field(f"{name_prefix}_label", state.t("label.field_label"), state.t("hint.dynamic_label", header=header), first_field.get("label", ""))
                val_field = _apple_field(f"{name_prefix}_value", state.t("label.field_value"), state.t("hint.dynamic_value", header=header), first_field.get("value", ""))
                container.controls.append(ft.Row([lbl_field, val_field], spacing=10))

            def update_apple_preview():
                p_data_copy = passes_current_json.copy()
                pass_data = {}
                
                if "holder_name" in apple_edit_refs and apple_edit_refs["holder_name"].current:
                    p_data_copy["holder_name"] = apple_edit_refs["holder_name"].current.value
                if "holder_email" in apple_edit_refs and apple_edit_refs["holder_email"].current:
                    p_data_copy["holder_email"] = apple_edit_refs["holder_email"].current.value

                if apple_edit_refs.get("background_color") and apple_edit_refs["background_color"].current:
                     pass_data["hexBackgroundColor"] = apple_edit_refs["background_color"].current.value
                     pass_data["bg_color"] = apple_edit_refs["background_color"].current.value

                visual_data = p_data.get("visual_data", {}).copy()
                if "apple_org_name" in apple_edit_refs and apple_edit_refs["apple_org_name"].current:
                    visual_data["organization_name"] = apple_edit_refs["apple_org_name"].current.value
                    pass_data["card_title"] = apple_edit_refs["apple_org_name"].current.value

                if "apple_logo_url" in apple_edit_refs and apple_edit_refs["apple_logo_url"].current:
                    visual_data["logo_url"] = apple_edit_refs["apple_logo_url"].current.value
                    pass_data["logo_url"] = apple_edit_refs["apple_logo_url"].current.value

                if "apple_strip_url" in apple_edit_refs and apple_edit_refs["apple_strip_url"].current:
                    visual_data["strip_url"] = apple_edit_refs["apple_strip_url"].current.value
                    pass_data["hero_image"] = apple_edit_refs["apple_strip_url"].current.value

                def safe_preview(lbl_k, val_k, mod_k):
                    lbl = apple_edit_refs[lbl_k].current.value if lbl_k in apple_edit_refs and apple_edit_refs[lbl_k].current else ""
                    val = apple_edit_refs[val_k].current.value if val_k in apple_edit_refs and apple_edit_refs[val_k].current else ""
                    if lbl or val:
                        return {"id": mod_k, "header": lbl, "body": val}
                    return None
                
                textModulesData = []
                for lbl_k, val_k, mod_k in [
                    ("apple_primary_label", "apple_primary_value", "apple_primary"),
                    ("apple_sec_label", "apple_sec_value", "apple_sec"),
                    ("apple_aux_label", "apple_aux_value", "apple_aux"),
                    ("apple_back_label", "apple_back_value", "apple_back"),
                ]:
                    mod = safe_preview(lbl_k, val_k, mod_k)
                    if mod: textModulesData.append(mod)
                
                if textModulesData:
                    pass_data["textModulesData"] = textModulesData

                # Reactive sync to shared MobileMockupPreview
                preview.update_data(pass_data, "apple")
                
                page.update()

            visual_data = p_data.get("visual_data", {})
            
            passes_form_container.controls.extend([
                ft.Container(content=ft.Text(state.t("label.step_pass_holder"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5)),
                _apple_field("holder_name", state.t("label.holder_name"), state.t("hint.john_doe"), p_data.get("holder_name", "")),
                _apple_field("holder_email", state.t("label.holder_email"), state.t("hint.john_email"), p_data.get("holder_email", "")),

                ft.Container(content=ft.Text(state.t("label.step_customize_color"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5))
            ])

            class AppleColorState:
                def __init__(self, col): self.color = col
                def get(self, k, default=None): return self.color if k == "background_color" else default
                def update(self, k, v):
                    if k == "background_color": 
                        self.color = v
                        mock_ref = type('obj', (object,), {'value' : v})
                        apple_edit_refs["background_color"].current = mock_ref
                        update_apple_preview()

            apple_col = visual_data.get("background_color") or "#4285f4"
            cp = create_color_picker(page, AppleColorState(apple_col), lambda: None)
            passes_form_container.controls.append(cp)
            apple_edit_refs["background_color"] = ft.Ref()
            apple_edit_refs["background_color"].current = type('obj', (object,), {'value' : apple_col})

            passes_form_container.controls.extend([
                ft.Container(content=ft.Text(state.t("label.step_pass_details"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5)),
                _apple_field("apple_org_name", state.t("label.organization_name"), state.t("hint.my_company"), visual_data.get("organization_name", "")),
                _apple_field("apple_logo_text", state.t("label.logo_text"), state.t("hint.pass"), visual_data.get("logo_text", "")),
                _apple_field("apple_logo_url", state.t("label.logo_icon_url"), state.t("hint.logo_url"), visual_data.get("logo_url", "")),
                _apple_field("apple_strip_url", state.t("label.strip_hero_image_url"), state.t("hint.strip_url"), visual_data.get("strip_url", "")),

                ft.Container(content=ft.Text(state.t("label.step_top_row"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5)),
            ])
            _apple_pair("apple_header", "header_fields", passes_form_container)

            passes_form_container.controls.append(ft.Container(content=ft.Text(state.t("label.step_info_rows"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5)))
            passes_form_container.controls.append(ft.Text(state.t("label.primary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _apple_pair("apple_primary", "primary_fields", passes_form_container)
            passes_form_container.controls.append(ft.Text(state.t("label.secondary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _apple_pair("apple_sec", "secondary_fields", passes_form_container)
            passes_form_container.controls.append(ft.Text(state.t("label.auxiliary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _apple_pair("apple_aux", "auxiliary_fields", passes_form_container)
            passes_form_container.controls.append(ft.Text(state.t("label.back_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _apple_pair("apple_back", "back_fields", passes_form_container)

            update_apple_preview()
            
            _set_status(state.t("msg.template_loaded"))
            page.update()

        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_and_sync_pass_handler(e):
        if not passes_object_id_field.value:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return

        _set_status("⏳ Updating and regenerating Apple pass...", "blue"); page.update()
        try:
            object_id = passes_object_id_field.data
            
            def safe_field(label_ref, value_ref, key_name):
                if label_ref in apple_edit_refs and value_ref in apple_edit_refs:
                    if apple_edit_refs[label_ref].current and apple_edit_refs[value_ref].current:
                        l = apple_edit_refs[label_ref].current.value
                        v = apple_edit_refs[value_ref].current.value
                        if l and v:
                            return [{"key": key_name, "label": l, "value": v}]
                return []

            def get_val(key):
                if key in apple_edit_refs and apple_edit_refs[key].current:
                    val = apple_edit_refs[key].current.value
                    return val if val else None
                return None

            store_card_data = {
                "background_color": get_val("background_color"),
                "logo_url": get_val("apple_logo_url"),
                "icon_url": get_val("apple_logo_url"),
                "strip_url": get_val("apple_strip_url"),
                "organization_name": get_val("apple_org_name"),
                "logo_text": get_val("apple_logo_text"),
                "header_fields": safe_field("apple_header_label", "apple_header_value", "header"),
                "primary_fields": safe_field("apple_primary_label", "apple_primary_value", "primary"),
                "secondary_fields": safe_field("apple_sec_label", "apple_sec_value", "secondary1"),
                "auxiliary_fields": safe_field("apple_aux_label", "apple_aux_value", "aux1"),
                "back_fields": safe_field("apple_back_label", "apple_back_value", "back1"),
            }
            
            holder_name = get_val("holder_name") or "Apple Holder"
            holder_email = get_val("holder_email") or "apple@example.com"
            
            if hasattr(api_client, "update_apple_pass"):
                api_client.update_apple_pass(
                    serial_number=object_id,
                    holder_name=holder_name,
                    holder_email=holder_email,
                    store_card_data=store_card_data
                )
            
            from services.apple_wallet_service import AppleWalletService
            apple_service = AppleWalletService()
            
            class_id = passes_class_id_field.data
            class_data = api_client.get_class(class_id)

            pass_data_for_generator = {}
            pass_data_for_generator["logo_url"] = store_card_data["logo_url"]
            pass_data_for_generator["hero_image"] = store_card_data["strip_url"]
            pass_data_for_generator["card_title"] = store_card_data["organization_name"]
            pass_data_for_generator["hexBackgroundColor"] = store_card_data["background_color"]
            
            tm = []
            for lbl_k, val_k, mod_k in [
                ("apple_primary_label", "apple_primary_value", "apple_primary"),
                ("apple_sec_label", "apple_sec_value", "apple_sec"),
                ("apple_aux_label", "apple_aux_value", "apple_aux"),
                ("apple_back_label", "apple_back_value", "apple_back"),
            ]:
                lbl = get_val(lbl_k)
                val = get_val(val_k)
                if lbl or val:
                    tm.append({"id": mod_k, "header": lbl, "body": val})
            if tm:
                pass_data_for_generator["textModulesData"] = tm

            apple_pass_path = apple_service.create_pass(
                class_data=class_data,
                pass_data=pass_data_for_generator,
                object_id=object_id,
            )
            
            _set_status(f"✅ Apple pass updated and generated! Saved at: {apple_pass_path}", "green")
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def generate_save_link_handler(e):
        try:
            import os, platform as platform_mod, subprocess
            from configs import APPLE_PASSES_OUTPUT_DIR
            apple_folder = APPLE_PASSES_OUTPUT_DIR
            
            if platform_mod.system() == "Windows":
                os.startfile(apple_folder)
            elif platform_mod.system() == "Darwin":
                subprocess.call(["open", apple_folder])
            else:
                subprocess.call(["xdg-open", apple_folder])
            _set_status("✅ Opened Apple Passes folder", "green")
        except Exception as ex:
            _set_status(f"❌ Error opening folder: {ex}", "red")
        page.update()


    # ── Startup ──
    load_passes_classes()

    left_panel = ft.Container(
        expand=True,
        content=ft.Column([
            ft.Text("Manage Apple Passes", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.manage_passes"), size=11, color="grey"),
            ft.Divider(),

            ft.Text("1. " + state.t("label.select_template"), size=13, weight=ft.FontWeight.W_500, color="blue700"),
            manage_passes_class_dropdown,
            ft.Container(height=5),
            ft.Text("2. " + state.t("label.select_pass"), size=13, weight=ft.FontWeight.W_500, color="blue700"),
            manage_passes_dropdown,
            ft.ElevatedButton(
                state.t("btn.load_pass"), icon="download", on_click=show_pass, width=380,
                style=ft.ButtonStyle(bgcolor="green", color="white"),
            ),
            passes_status,
            ft.Divider(height=20),
            ft.Container(height=5),
            passes_form_container,
            ft.Divider(height=20),
            ft.ElevatedButton(
                "Update & Generate Apple Pass", icon="cloud_sync",
                on_click=update_and_sync_pass_handler, width=380,
                style=ft.ButtonStyle(bgcolor="blue", color="white"),
            ),
            ft.Container(height=10),
            ft.ElevatedButton(
                text="Open Apple Folder", icon="folder_open",
                on_click=generate_save_link_handler, width=380,
                style=ft.ButtonStyle(bgcolor="green", color="white"),
            ),
            ft.Container(height=10),
            passes_result_container,
        ], spacing=8, scroll="auto"),
        padding=15, bgcolor="white",
    )

    return ft.Container(
        content=left_panel,
        expand=True,
        padding=15,
        bgcolor="white"
    )
