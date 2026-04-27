"""
Google Pass Generator View
Google-specific pass generation form with live mobile mockup preview.
All backend logic transplanted from ui/pass_generator.py (Google branch).
"""

import flet as ft
import os
import subprocess
import platform as platform_mod
import time
import httpx
from typing import Dict, List, Any, Optional

from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR
from ui.components.mobile_mockup import MobileMockupPreview
from ui.components.preview_builder import build_comprehensive_preview
from ui.components.color_picker import create_color_picker
from core.qr_generator import generate_qr_code
import configs


# Field configurations per pass type
PASS_TYPE_FIELDS = {
    "Generic": [
        {"name": "logo_url",        "label": "label.logo_url",        "type": "text", "hint": "e.g., https://example.com/logo.png", "section": "Header"},
        {"name": "hero_image_url",   "label": "Hero Image URL",       "type": "text", "hint": "e.g., https://example.com/hero.png",  "section": "Header"},
        {"name": "card_title",       "label": "label.issuer_name",    "type": "text", "hint": "e.g., Your Business Name",            "section": "Header"},
        {"name": "subheader_value",  "label": "label.subheader_value","type": "text", "hint": "e.g., VIP Level",                     "section": "Top Row"},
        {"name": "header_value",     "label": "label.header_value",   "type": "text", "hint": "e.g., VIP Member",                    "section": "Top Row"},
    ],
    "EventTicket": [
        {"name": "event_date",   "label": "label.event_date",   "type": "text", "hint": "e.g., 2024-12-25",   "template_field": True},
        {"name": "event_time",   "label": "label.event_time",   "type": "text", "hint": "e.g., 19:00",        "template_field": True},
        {"name": "seat_number",  "label": "label.seat_number",  "type": "text", "hint": "e.g., A12"},
        {"name": "section",      "label": "label.section",      "type": "text", "hint": "e.g., Lower Bowl"},
        {"name": "gate",         "label": "label.gate",         "type": "text", "hint": "e.g., Gate 3"},
    ],
    "LoyaltyCard": [
        {"name": "points_balance",    "label": "label.points_balance",    "type": "number", "hint": "e.g., 1500"},
        {"name": "tier_level",        "label": "label.tier_level",        "type": "text",   "hint": "e.g., Gold"},
        {"name": "member_since",      "label": "label.member_since",      "type": "text",   "hint": "e.g., 2024-01-15"},
        {"name": "rewards_available", "label": "label.rewards_available", "type": "number", "hint": "e.g., 3"},
    ],
    "GiftCard": [
        {"name": "balance",     "label": "label.card_balance", "type": "number", "hint": "e.g., 50.00"},
        {"name": "card_number", "label": "label.card_number",  "type": "text",   "hint": "e.g., 1234-5678-9012"},
        {"name": "expiry_date", "label": "label.expiry_date",  "type": "text",   "hint": "e.g., 2025-12-31"},
    ],
    "TransitPass": [
        {"name": "pass_type",   "label": "label.pass_type",   "type": "text", "hint": "e.g., Monthly Pass"},
        {"name": "valid_from",  "label": "label.valid_from",   "type": "text", "hint": "e.g., 2024-12-01"},
        {"name": "valid_until", "label": "label.valid_until",  "type": "text", "hint": "e.g., 2024-12-31"},
        {"name": "zones",       "label": "label.zones",        "type": "text", "hint": "e.g., Zone 1-3"},
    ],
}


def build_google_generator_view(page: ft.Page, state, api_client, wallet_client, preview: MobileMockupPreview):
    """
    Build the Google Pass Generator view.

    Returns an ft.Row with [form_panel, preview_panel].
    """
    # ── Refs ──
    template_dropdown_ref = ft.Ref[ft.Dropdown]()
    holder_name_ref       = ft.Ref[ft.TextField]()
    holder_email_ref      = ft.Ref[ft.TextField]()
    message_type_ref      = ft.Ref[ft.Dropdown]()
    status_ref            = ft.Ref[ft.Text]()

    dynamic_field_refs: dict = {}
    current_class_data = None
    
    custom_color_state = {"background_color": "#4285f4"}
    
    bg_color_picker_container = ft.Container(content=None)
    class_metadata: dict = {}
    json_editor = None

    # ── Preview sync ──
    def _sync_preview():
        if not current_class_data:
            return
        data = {
            "bg_color":       custom_color_state.get("background_color", "#4285f4"),
            "holder_name":    holder_name_ref.current.value if holder_name_ref.current else "",
        }
        for field_name, field_ref in dynamic_field_refs.items():
            if field_ref.current:
                val = field_ref.current.value or ""
                data[field_name] = val
                # Map to mockup keys
                if field_name == "logo_url":
                    data["logo_url"] = val
                elif field_name == "hero_image_url":
                    data["hero_image_url"] = val
                elif field_name == "card_title":
                    data["issuer_name"] = val
                elif field_name == "header_value":
                    data["header"] = val
                elif field_name == "subheader_value":
                    data["subheader"] = val

        class_type = current_class_data.get("class_type", "Generic")
        if class_type == "Generic":
            text_modules = _collect_text_modules()
            if text_modules:
                data["textModulesData"] = text_modules

        preview.update_data(data, "google")

    def _on_color():
        _sync_preview()

    # ── Text modules collector ──
    def _collect_text_modules() -> list:
        text_modules = []
        if not current_class_data:
            return text_modules
        template_rows = current_class_data.get("text_module_rows", [])
        for row in template_rows:
            row_idx = row.get("row_index", 0)
            for col, hdr_key in [("left", "left_header"), ("middle", "middle_header"), ("right", "right_header")]:
                header_text = row.get(hdr_key)
                field_id = f"row_{row_idx}_{col}"
                if header_text and field_id in dynamic_field_refs and dynamic_field_refs[field_id].current:
                    val = dynamic_field_refs[field_id].current.value
                    m_type = row.get(f"{col}_type", "text")
                    if val:
                        text_modules.append({"id": field_id, "header": header_text, "body": val, "module_type": m_type})
        return text_modules

    # ── File Picker Logic ──
    current_picker_target = None
    
    def on_file_result(e: ft.FilePickerResultEvent):
        nonlocal current_picker_target
        if e.files and current_picker_target:
            file = e.files[0]
            try:
                # Get the API base URL from configs or deduce it
                api_url = getattr(configs, "API_BASE_URL", "http://localhost:8000")
                upload_endpoint = f"{api_url}/upload/image"
                
                # Upload the file
                with open(file.path, "rb") as f:
                    files = {"file": (file.name, f)}
                    response = httpx.post(upload_endpoint, files=files)
                    
                if response.status_code == 200:
                    uploaded_url = response.json().get("url")
                    current_picker_target.value = uploaded_url
                    current_picker_target.update()
                    # Trigger visual sync
                    _sync_preview()
                else:
                    print(f"Upload failed: {response.text}")
            except Exception as ex:
                print(f"File picker error: {ex}")
        current_picker_target = None

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def pick_image_for(target_tf):
        nonlocal current_picker_target
        current_picker_target = target_tf
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # ── Build form fields ──
    def build_form_fields():
        if not current_class_data:
            return
        class_type = current_class_data.get("class_type", "Generic")
        dynamic_field_refs.clear()
        
        # Holder info section
        holder_info_section = card(ft.Column([
            section_title("Pass Holder Information", ft.Icons.PERSON),
            ft.Row([
                ft.TextField(
                    ref=holder_name_ref,
                    label="Holder Name",
                    hint_text="e.g., John Doe", expand=1, border_radius=8, text_size=13,
                    on_change=lambda e: _sync_preview(),
                ),
                ft.TextField(
                    ref=holder_email_ref,
                    label="Holder Email",
                    hint_text="e.g., john@example.com", expand=1, border_radius=8, text_size=13,
                ),
            ], spacing=12),
            ft.Dropdown(
                ref=message_type_ref,
                label="Notification Type",
                width=380, value="TEXT_AND_NOTIFY", border_radius=8, text_size=13,
                options=[
                    ft.dropdown.Option(key="TEXT", text="No Notification"),
                    ft.dropdown.Option(key="TEXT_AND_NOTIFY", text="Send Push Notification"),
                ],
            ),
        ], spacing=8))

        # Color picker section
        colors_section = card(ft.Column([
            section_title("Customize Color", ft.Icons.PALETTE),
            bg_color_picker_container,
        ], spacing=8))

        # Pass details section
        details_controls = [
            section_title("Pass Details", ft.Icons.DESCRIPTION),
        ]

        fields_config = PASS_TYPE_FIELDS.get(class_type, [])
        current_section = None
        for field_config in fields_config:
            if "section" in field_config and field_config["section"] != current_section:
                current_section = field_config["section"]
                details_controls.append(
                    ft.Container(
                        content=ft.Text(current_section, size=14, weight=ft.FontWeight.W_600, color=PRIMARY),
                        padding=ft.padding.only(top=8, bottom=4),
                    )
                )

            field_ref = ft.Ref[ft.TextField]()
            dynamic_field_refs[field_config["name"]] = field_ref

            initial_value = ""
            is_readonly = False
            if class_type == "Generic":
                if field_config["name"] == "logo_url" and current_class_data.get("logo_url"):
                    initial_value = current_class_data.get("logo_url")
                elif field_config["name"] == "hero_image_url" and current_class_data.get("hero_image_url"):
                    initial_value = current_class_data.get("hero_image_url")
                elif field_config["name"] == "card_title" and current_class_data.get("card_title"):
                    initial_value = current_class_data.get("card_title")
                elif field_config["name"] == "header_value" and current_class_data.get("header_text"):
                    initial_value = current_class_data.get("header_text")

            if field_config.get("template_field", False):
                is_readonly = True
                class_json = current_class_data.get("class_json", {})
                dt_obj = class_json.get("dateTime", {})
                start_dt = dt_obj.get("start", "")
                if "T" in start_dt:
                    t_date, t_time = start_dt.split("T")
                    t_time = t_time[:5]
                else: t_date = t_time = ""
                if field_config["name"] == "event_date" and t_date: initial_value = t_date
                elif field_config["name"] == "event_time" and t_time: initial_value = t_time

            tf = ft.TextField(
                ref=field_ref,
                label=state.t(field_config["label"]) if state.t(field_config["label"]) != field_config["label"] else field_config["label"].replace("label.", "").replace("_", " ").title(),
                hint_text=field_config["hint"],
                value=initial_value, read_only=is_readonly,
                border_radius=8, text_size=13, expand=True,
                on_change=lambda e: _sync_preview(),
            )
            
            # If it's an image field, add an upload button
            is_image_field = "url" in field_config["name"].lower() or "image" in field_config["name"].lower()
            if is_image_field and not is_readonly:
                details_controls.append(ft.Row([
                    tf,
                    ft.IconButton(
                        icon=ft.Icons.IMAGE_SEARCH_ROUNDED,
                        tooltip=f"Select {field_config['label']}",
                        on_click=lambda e, target=tf: pick_image_for(target)
                    )
                ], spacing=5))
            else:
                details_controls.append(tf)

        details_section = card(ft.Column(details_controls, spacing=8))

        # Information Fields section
        info_section = None
        if class_type == "Generic":
            template_rows = current_class_data.get("text_module_rows", [])
            if template_rows:
                info_controls = [section_title("Information Fields", ft.Icons.TABLE_ROWS)]
                for row in template_rows:
                    row_idx = row.get("row_index", 0)
                    fields_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.START)

                    def _add_field(col_name, header_key, parent_row, _row=row, _row_idx=row_idx):
                        header_text = _row.get(header_key)
                        m_type = _row.get(f"{col_name}_type", "text")
                        if header_text:
                            fid = f"row_{_row_idx}_{col_name}"
                            fref = ft.Ref[ft.TextField]()
                            dynamic_field_refs[fid] = fref
                            
                            hint = f"Enter {header_text}"
                            if m_type == "link":
                                hint = f"Enter URL for {header_text}"
                                
                            parent_row.controls.append(
                                ft.TextField(
                                    ref=fref, label=header_text,
                                    hint_text=hint,
                                    expand=True, border_radius=8, text_size=13,
                                    multiline=m_type != "link", 
                                    min_lines=3 if m_type != "link" else 1,
                                    max_lines=10 if m_type != "link" else 1,
                                    on_change=lambda e: _sync_preview(),
                                )
                            )

                    _add_field("left",   "left_header",   fields_row)
                    _add_field("middle", "middle_header", fields_row)
                    _add_field("right",  "right_header",  fields_row)

                    if fields_row.controls:
                        info_controls.append(ft.Container(content=fields_row, padding=ft.padding.only(bottom=5)))
                
                info_section = card(ft.Column(info_controls, spacing=8))

        # Assemble final column
        final_controls = [holder_info_section, colors_section, details_section]
        if info_section:
            final_controls.append(info_section)
        
        # Add generate button and status at the end
        final_controls.extend([
            ft.Container(height=8),
            ft.ElevatedButton(
                state.t("btn.generate_pass"), icon=ft.Icons.ROCKET_LAUNCH,
                on_click=generate_pass,
                bgcolor=PRIMARY, color="white", height=48, width=240,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            ft.Text(ref=status_ref, value="", size=12),
        ])

        form_controls_column.controls = final_controls
        form_controls_column.visible = True
        page.update()

    # ── Template selection ──
    def on_template_selected(e):
        if not template_dropdown_ref.current.value:
            return
        try:
            nonlocal current_class_data
            class_id = template_dropdown_ref.current.value

            if class_id in class_metadata:
                class_data = class_metadata[class_id]
            else:
                class_data = api_client.get_class(class_id) if api_client else None
                if not class_data:
                    if status_ref.current:
                        status_ref.current.value = state.t("msg.template_not_found", id=class_id)
                        status_ref.current.color = "red"
                    page.update()
                    return
                class_metadata[class_id] = class_data

            current_class_data = class_data
            class_type = class_data.get("class_type", "Generic")
            class_json = class_data.get("class_json", {})

            base_color = class_data.get("base_color") or class_json.get("hexBackgroundColor", "#4285f4")
            logo_url = class_data.get("logo_url")
            if not logo_url and "logo" in class_json:
                logo_url = class_json.get("logo", {}).get("sourceUri", {}).get("uri")
            elif not logo_url and "programLogo" in class_json:
                logo_url = class_json.get("programLogo", {}).get("sourceUri", {}).get("uri")

            header_text = class_data.get("header_text") or class_data.get("issuer_name", state.t("placeholder.business_name"))
            if not header_text or header_text == state.t("placeholder.business_name"):
                if "localizedIssuerName" in class_json:
                    header_text = class_json.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
                elif "issuerName" in class_json:
                    header_text = class_json.get("issuerName", "Business")

            card_title = class_data.get("card_title", state.t("placeholder.pass_title"))
            if not card_title or card_title == state.t("placeholder.pass_title"):
                if "localizedProgramName" in class_json:
                    card_title = class_json.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
                elif "eventName" in class_json:
                    card_title = class_json.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
                elif "cardTitle" in class_json:
                    card_title = class_json.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")

            current_class_data.update({
                "class_type": class_type, "class_id": class_id,
                "base_color": base_color, "logo_url": logo_url,
                "header_text": header_text, "card_title": card_title,
            })

            custom_color_state["background_color"] = base_color

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
            bg_color_picker_container.content = create_color_picker(page, color_state_obj, _on_color, "background_color", "Background Color")

            build_form_fields()
            if status_ref.current:
                status_ref.current.value = state.t("msg.loaded_template_type", type=class_type)
                status_ref.current.color = "green"
            _sync_preview()
        except Exception as ex:
            import traceback; traceback.print_exc()
            if status_ref.current:
                status_ref.current.value = f"❌ Error: {str(ex)}"
                status_ref.current.color = "red"
        page.update()

    def reset_form(e=None):
        """Reset the generation form to its initial state."""
        template_dropdown_ref.current.value = None
        holder_name_ref.current.value = ""
        holder_email_ref.current.value = ""
        message_type_ref.current.value = "TEXT_AND_NOTIFY"
        status_ref.current.value = ""
        
        # Clear dynamic fields
        for ref in dynamic_field_refs.values():
            if ref.current:
                ref.current.value = ""
        
        # Hide the form controls until next template selection
        form_controls_column.visible = False
        _sync_preview()
        page.update()

    # ── Load templates ──
    def load_templates():
        try:
            classes = api_client.get_classes() if api_client else []
            if classes and len(classes) > 0:
                class_metadata.clear()
                for cls in classes:
                    class_metadata[cls["class_id"]] = cls
                template_dropdown_ref.current.options = [
                    ft.dropdown.Option(
                        key=cls["class_id"],
                        text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})",
                    )
                    for cls in classes
                ]
                if status_ref.current:
                    status_ref.current.value = ""
            else:
                template_dropdown_ref.current.options = []
                if status_ref.current:
                    status_ref.current.value = state.t("msg.no_templates")
                    status_ref.current.color = "blue"
            page.update()
        except Exception as e:
            if status_ref.current:
                status_ref.current.value = f"❌ Error loading templates: {e}"
                status_ref.current.color = "red"

    state.register_refresh_callback("pass_generator_templates", load_templates)

    # ── Generate pass ──
    def generate_pass(e):
        if not template_dropdown_ref.current.value:
            status_ref.current.value = state.t("msg.pls_select_template")
            status_ref.current.color = "red"; page.update(); return
        if not holder_name_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_name")
            status_ref.current.color = "red"; page.update(); return
        if not holder_email_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_email")
            status_ref.current.color = "red"; page.update(); return

        # Ensure card_title (Issuer Name) is set for Generic passes
        class_id = template_dropdown_ref.current.value
        class_type = current_class_data.get("class_type", "Generic")
        if class_type == "Generic":
             card_title = dynamic_field_refs.get("card_title")
             if card_title and not card_title.current.value:
                 # Auto-fill with a fallback if empty to prevent Google API error
                 card_title.current.value = class_id or "Pass"
                 card_title.current.update()

        if status_ref.current:
            status_ref.current.value = "⏳ Generating pass..."
            status_ref.current.color = "blue"
        page.update()

        try:
            pass_data = {}
            for field_name, field_ref in dynamic_field_refs.items():
                if field_ref.current and field_ref.current.value:
                    pass_data[field_name] = field_ref.current.value
            custom_color = custom_color_state.get("background_color")
            if custom_color:
                pass_data["hexBackgroundColor"] = custom_color

            class_type = current_class_data.get("class_type", "Generic")
            if class_type == "Generic":
                text_modules_data = _collect_text_modules()
                if text_modules_data:
                    pass_data["textModulesData"] = text_modules_data

            timestamp = int(time.time())
            clean_name = holder_name_ref.current.value.replace(' ', '_').lower()
            object_suffix = f"pass_{timestamp}_{clean_name}"
            object_id = f"{configs.ISSUER_ID}.{object_suffix}"

            class_id = template_dropdown_ref.current.value
            if not class_id.startswith(configs.ISSUER_ID):
                class_id = f"{configs.ISSUER_ID}.{class_id}"

            message_type = message_type_ref.current.value if message_type_ref.current else "TEXT_AND_NOTIFY"

            if class_type == "Generic":
                msg_id = f"create_msg_{timestamp}"
                pass_data["messages"] = [{
                    "id": msg_id, "header": "Welcome",
                    "body": "Your pass has been created", "messageType": message_type,
                }]

            if status_ref.current:
                status_ref.current.value = state.t("msg.creating_in_google")
                status_ref.current.color = "blue"
            page.update()

            if class_type == "EventTicket":
                google_pass_object = wallet_client.build_event_ticket_object(
                    object_id=object_id, class_id=class_id,
                    holder_name=holder_name_ref.current.value, holder_email=holder_email_ref.current.value,
                    pass_data=pass_data, custom_color=custom_color, message_type=message_type,
                )
            elif class_type == "LoyaltyCard":
                google_pass_object = wallet_client.build_loyalty_object(
                    object_id=object_id, class_id=class_id,
                    holder_name=holder_name_ref.current.value, holder_email=holder_email_ref.current.value,
                    pass_data=pass_data, custom_color=custom_color, message_type=message_type,
                )
            else:
                google_pass_object = wallet_client.build_generic_object(
                    object_id=object_id, class_id=class_id,
                    holder_name=holder_name_ref.current.value, holder_email=holder_email_ref.current.value,
                    pass_data=pass_data, custom_color=custom_color, message_type=None,
                )

            wallet_client.create_pass_object(google_pass_object, class_type)
            save_link = wallet_client.generate_save_link(object_id, class_type, class_id)

            db_saved = False
            try:
                db_class_id = class_id.split('.')[-1] if '.' in class_id else class_id
                api_client.create_pass(
                    object_id=object_id, class_id=db_class_id,
                    holder_name=holder_name_ref.current.value, holder_email=holder_email_ref.current.value,
                    status="Active", pass_data=pass_data,
                )
                db_saved = True
                state.refresh_ui("manage_passes_list")
                state.refresh_ui("send_notification_list")
            except Exception as db_error:
                print(f"Warning: Could not save to local database: {db_error}")

            qr_filename = f"pass_qr_{int(time.time())}"
            # Save to static directory so it's accessible via public URL
            static_qr_dir = os.path.join(os.getcwd(), "static", "qrcodes")
            os.makedirs(static_qr_dir, exist_ok=True)
            
            # Generate QR code
            qr_image_path = generate_qr_code(save_link, qr_filename, assets_dir=static_qr_dir)
            
            # Public URL for the image
            public_qr_url = f"{configs.PUBLIC_URL}/static/qrcodes/{qr_filename}.png"

            # --- Success Dialog ---
            def dialog_dismissed(e):
                reset_form()

            def close_dlg(e):
                page.close(success_dlg)

            success_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Pass Generated Successfully!", weight=ft.FontWeight.BOLD),
                content=ft.Column([
                    ft.Text("Scan the QR code or click the link below to add the pass to Google Wallet.", size=13),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Image(src=public_qr_url, width=200, height=200, fit=ft.ImageFit.CONTAIN),
                        alignment=ft.alignment.center, bgcolor="white", border_radius=10, padding=10,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add to Google Wallet",
                        icon=ft.Icons.ADD_CARD,
                        on_click=lambda e: page.launch_url(save_link),
                        bgcolor="blue", color="white",
                        width=250,
                    ),
                    ft.Container(height=5),
                    ft.Text(f"Object ID: {object_id}", size=10, color="grey"),
                ], tight=True, width=300, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                on_dismiss=dialog_dismissed,
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            
            page.open(success_dlg)

            if status_ref.current:
                status_ref.current.value = state.t("status.pass_generated_google")
                status_ref.current.color = "green"
        except Exception as ex:
            import traceback; traceback.print_exc()
            if status_ref.current:
                status_ref.current.value = f"❌ Error: {str(ex)}"
                status_ref.current.color = "red"
        page.update()

    # ── Build form layout ──
    form_controls_column = ft.Column(visible=False, spacing=12)

    form_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        content=ft.Column([
            ft.Text("Google Pass Generator", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Fill in the fields below to generate a Google Wallet pass.", color=TEXT_SECONDARY, size=13),
            ft.Container(height=8),

            ft.Dropdown(
                ref=template_dropdown_ref,
                label=state.t("label.class_id"),
                hint_text=state.t("label.select_class_err"),
                width=380, border_radius=8, text_size=13,
                on_change=on_template_selected,
            ),
            
            form_controls_column,
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True),
    )

    # Load templates on start
    load_templates()

    # Initialise the preview
    preview.update_data({"bg_color": "#4285f4"}, "google")

    return form_panel
