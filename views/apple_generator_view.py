"""
Apple Pass Generator View
Apple-specific StoreCard pass generation form with live mobile mockup preview.
All backend logic transplanted from ui/pass_generator.py (Apple branch).
"""

import flet as ft
import os
import subprocess
import platform as platform_mod
import time
import secrets
from typing import Dict

from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR, SECTION_HEADER
from ui.components.mobile_mockup import MobileMockupPreview
from ui.components.color_picker import create_color_picker
from ui.components.apple_field_editor import AppleFieldEditor
import configs


def build_apple_generator_view(page: ft.Page, state, api_client, preview: MobileMockupPreview):
    """
    Build the Apple Pass Generator view.

    Returns an ft.Container (form panel). The preview panel is managed by root_view.
    """
    # ── Refs ──
    title_ref     = ft.Ref[ft.TextField]()
    holder_name_ref  = ft.Ref[ft.TextField]()
    holder_email_ref = ft.Ref[ft.TextField]()
    status_ref       = ft.Ref[ft.Text]()
    result_container_ref = ft.Ref[ft.Container]()

    dynamic_field_refs: dict = {}
    custom_color_state = {
        "background_color": "#1a1a2e",
        "foreground_color": "#ffffff",
        "label_color": "#bbbbbb"
    }
    bg_color_picker_container = ft.Container(content=None)
    fg_color_picker_container = ft.Container(content=None)
    lbl_color_picker_container = ft.Container(content=None)

    # We still need a class_id for DB storage — Apple reuses Google class dropdown
    # For now we use a simple text field for pass title / ID
    current_class_data = None

    # ── AppleFieldEditor ──
    apple_field_editor = AppleFieldEditor(on_change=None)  # We will set on_change after _sync_preview is defined

    # ── Preview sync ──
    def _sync_preview(_=None):
        data = {
            "bg_color":     custom_color_state.get("background_color", "#1a1a2e"),
            "fg_color":     custom_color_state.get("foreground_color", "#ffffff"),
            "label_color":  custom_color_state.get("label_color", "#bbbbbb"),
            "holder_name":  holder_name_ref.current.value  if holder_name_ref.current  else "",
        }
        for key, ref in dynamic_field_refs.items():
            if ref.current:
                data[key] = ref.current.value or ""
        # Map to mockup keys
        if "apple_org_name" in data:
            data["org_name"] = data["apple_org_name"]
        if "apple_logo_text" in data:
            data["logo_text"] = data["apple_logo_text"]
        if "apple_strip_url" in data:
            data["strip_url"] = data["apple_strip_url"]
            
        data["dynamic_fields"] = apple_field_editor.get_fields_data()
        preview.update_data(data, "apple")

    apple_field_editor.on_change = _sync_preview

    def _on_color():
        _sync_preview()

    # ── Open folder helper ──
    def _open_folder(folder_path):
        try:
            if platform_mod.system() == "Windows":
                os.startfile(folder_path)
            elif platform_mod.system() == "Darwin":
                subprocess.call(["open", folder_path])
            else:
                subprocess.call(["xdg-open", folder_path])
        except Exception as exc:
            print(f"Warning: Could not open folder: {exc}")

    # ── Color picker initialization ──
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

    color_state_obj = SimpleColorState(custom_color_state, _on_color)
    bg_color_picker_container.content = create_color_picker(
        page, color_state_obj, _on_color, "background_color", "Background Color"
    )
    fg_color_picker_container.content = create_color_picker(
        page, color_state_obj, _on_color, "foreground_color", "Foreground Color"
    )
    lbl_color_picker_container.content = create_color_picker(
        page, color_state_obj, _on_color, "label_color", "Label Color"
    )

    # ── Helper: get field values ──
    def _get_val(key):
        if key in dynamic_field_refs and dynamic_field_refs[key].current:
            val = dynamic_field_refs[key].current.value
            return val if val else None
        return None



    # ── Generate pass ──
    def generate_pass(e):
        if not holder_name_ref.current or not holder_name_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_name")
            status_ref.current.color = "red"; page.update(); return
        if not holder_email_ref.current or not holder_email_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_email")
            status_ref.current.color = "red"; page.update(); return

        status_ref.current.value = "⏳ Generating Apple Wallet pass..."
        status_ref.current.color = "blue"; page.update()

        try:
            pass_data = {}
            for field_name, field_ref in dynamic_field_refs.items():
                if field_ref.current and field_ref.current.value:
                    pass_data[field_name] = field_ref.current.value

            custom_color = custom_color_state.get("background_color")
            if custom_color:
                pass_data["hexBackgroundColor"] = custom_color

            pass_data["dynamic_fields"] = apple_field_editor.get_fields_data()

            timestamp = int(time.time())
            clean_name = holder_name_ref.current.value.replace(' ', '_').lower()
            object_id = f"pass_{timestamp}_{clean_name}"

            # Use selected template_id from dropdown
            template_id = template_dropdown.value
            if not template_id:
                status_ref.current.value = "⚠️ Please select a template first."
                status_ref.current.color = "orange"; page.update(); return

            from services.apple_wallet_service import AppleWalletService
            apple_service = AppleWalletService()

            # Build dummy class_data for the service (mostly for compatibility with existing create_pass)
            class_data_for_service = {
                "class_type": "Generic",
                "template_id": template_id,
                "base_color": custom_color,
            }

            apple_pass_path = apple_service.create_pass(
                class_data=class_data_for_service,
                pass_data=pass_data,
                object_id=object_id,
            )

            apple_folder = os.path.dirname(apple_pass_path)
            auth_token = secrets.token_hex(16)

            dynamic_fields = apple_field_editor.get_fields_data()
            def _extract_fields(ftype):
                return [{"key": f"{ftype}_{i}", "label": f["label"], "value": f["value"]}
                        for i, f in enumerate(dynamic_fields) if f["field_type"] == ftype]

            store_card_data = {
                "background_color": custom_color_state.get("background_color"),
                "foreground_color": custom_color_state.get("foreground_color"),
                "label_color":      custom_color_state.get("label_color"),
                "logo_url": _get_val("apple_logo_url"),
                "icon_url": _get_val("apple_logo_url"),
                "strip_url": _get_val("apple_strip_url"),
                "organization_name": _get_val("apple_org_name"),
                "logo_text": _get_val("apple_logo_text"),
                "primary_fields": _extract_fields("primary"),
                "secondary_fields": _extract_fields("secondary"),
                "auxiliary_fields": _extract_fields("auxiliary"),
                "back_fields": _extract_fields("back"),
            }

            db_saved = False
            try:
                api_client.create_apple_pass(
                    serial_number=object_id,
                    template_id=template_id,
                    pass_type_id=configs.APPLE_PASS_TYPE_ID,
                    holder_name=holder_name_ref.current.value,
                    holder_email=holder_email_ref.current.value,
                    auth_token=auth_token,
                    pass_data=pass_data,
                    store_card_data=store_card_data,
                )
                db_saved = True
                state.refresh_ui("manage_passes_list")
            except Exception as db_error:
                print(f"Warning: Could not save Apple pass to local database: {db_error}")

            result_container_ref.current.content = ft.Column([
                ft.Text("✅ Apple Pass Generated Successfully!", color="green", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                ft.Text(f"Saved at: {apple_pass_path}", size=10, color="grey", selectable=True),
                ft.Text(
                    f"{state.t('msg.saved_local_db') if db_saved else state.t('msg.not_saved_local_db')}",
                    size=10, color="green" if db_saved else "orange",
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    text=state.t("btn.open_apple_folder"),
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda e, folder=apple_folder: _open_folder(folder),
                    style=ft.ButtonStyle(bgcolor="black", color="white"),
                ),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            status_ref.current.value = "✅ Apple Wallet pass generated!"
            status_ref.current.color = "green"
        except Exception as ex:
            import traceback; traceback.print_exc()
            status_ref.current.value = f"❌ Error: {str(ex)}"
            status_ref.current.color = "red"
            result_container_ref.current.content = None
        page.update()

    # ── Apple-specific dynamic field refs ──
    for name in ["apple_org_name", "apple_logo_text", "apple_logo_url", "apple_strip_url"]:
        dynamic_field_refs[name] = ft.Ref[ft.TextField]()

    # ── Build UI ──
    template_dropdown = ft.Dropdown(
        label="Select Template",
        hint_text="Choose a template...",
        width=380, border_radius=8, text_size=13,
        options=[]
    )

    def load_templates():
        try:
            templates = api_client.get_apple_templates() if api_client else []
            if templates:
                template_dropdown.options = [
                    ft.dropdown.Option(t["template_id"], f"{t['template_name']} ({t['pass_style']})")
                    for t in templates
                ]
            else:
                template_dropdown.options = []
                template_dropdown.hint_text = "No Apple templates found."
        except Exception as e:
            print(f"Error loading Apple templates: {e}")
            template_dropdown.options = []
            template_dropdown.hint_text = "Error loading templates."
        if template_dropdown.page:
            template_dropdown.update()

    load_templates()
    if state:
        state.register_refresh_callback("apple_generator_templates", load_templates)

    form_controls_column = ft.Column(
        visible=False,
        spacing=12,
        controls=[
            # Pass Title
            card(ft.Column([
                section_title("Pass Identifier"),
                ft.TextField(
                    ref=title_ref, label="Pass Title / ID",
                    hint_text="e.g. store_card_vip",
                    width=380, border_radius=8, text_size=13,
                ),
            ], spacing=8)),

            # Holder info
            card(ft.Column([
                section_title(state.t("label.step_pass_holder"), ft.Icons.PERSON),
                ft.Row([
                    ft.TextField(
                        ref=holder_name_ref,
                        label=state.t("label.name_req") if state.t("label.name_req") != "label.name_req" else "Holder Name",
                        hint_text=state.t("hint.john_doe"), expand=1, border_radius=8, text_size=13,
                        on_change=_sync_preview,
                    ),
                    ft.TextField(
                        ref=holder_email_ref,
                        label=state.t("label.email_req") if state.t("label.email_req") != "label.email_req" else "Holder Email",
                        hint_text=state.t("hint.john_email"), expand=1, border_radius=8, text_size=13,
                    ),
                ], spacing=12),
            ], spacing=8)),

            # Colors
            card(ft.Column([
                section_title(state.t("label.step_customize_color"), ft.Icons.PALETTE),
                ft.Row([
                    bg_color_picker_container,
                    fg_color_picker_container,
                    lbl_color_picker_container,
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
            ], spacing=8)),

            # Brand assets
            card(ft.Column([
                section_title(state.t("label.step_pass_details"), ft.Icons.BRANDING_WATERMARK),
                ft.Row([
                    ft.TextField(
                        ref=dynamic_field_refs["apple_org_name"],
                        label=state.t("label.organization_name"), hint_text=state.t("hint.my_company"),
                        expand=1, border_radius=8, text_size=13, on_change=_sync_preview,
                    ),
                    ft.TextField(
                        ref=dynamic_field_refs["apple_logo_text"],
                        label=state.t("label.logo_text"), hint_text=state.t("hint.pass"),
                        expand=1, border_radius=8, text_size=13, on_change=_sync_preview,
                    ),
                ], spacing=12),
                ft.Row([
                    ft.TextField(
                        ref=dynamic_field_refs["apple_logo_url"],
                        label=state.t("label.logo_icon_url"), hint_text=state.t("hint.logo_url"),
                        expand=1, border_radius=8, text_size=13, on_change=_sync_preview,
                    ),
                    ft.TextField(
                        ref=dynamic_field_refs["apple_strip_url"],
                        label=state.t("label.strip_hero_image_url"), hint_text=state.t("hint.strip_url"),
                        expand=1, border_radius=8, text_size=13, on_change=_sync_preview,
                    ),
                ], spacing=12),
            ], spacing=8)),

            # StoreCard sections
            card(ft.Column([
                section_title("Card Fields", ft.Icons.VIEW_AGENDA),
                apple_field_editor.build(),
            ], spacing=8)),

            ft.Container(height=8),
            ft.ElevatedButton(
                "Generate Apple Pass", icon=ft.Icons.PHONE_IPHONE,
                on_click=generate_pass,
                bgcolor="#1a1a2e", color="white", height=48, width=240,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            ft.Text(ref=status_ref, value="", size=12),
            ft.Container(ref=result_container_ref, content=None),
        ]
    )

    def on_template_change(e):
        if template_dropdown.value:
            form_controls_column.visible = True
        else:
            form_controls_column.visible = False
        page.update()

    template_dropdown.on_change = on_template_change

    form_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        content=ft.Column([
            ft.Text("Apple Pass Generator", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Create a StoreCard pass for Apple Wallet.", color=TEXT_SECONDARY, size=13),
            ft.Container(height=8),
            template_dropdown,
            form_controls_column
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True),
    )

    # Initialise the preview
    preview.update_data({"bg_color": "#1a1a2e"}, "apple")

    return form_panel
