"""
Manage Passes View
Extracted from main.py — 3-panel layout for managing individual Google Wallet pass objects.
"""

import flet as ft
from ui.components.json_editor import JSONEditor
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
from ui.components.preview_builder import build_comprehensive_preview
from ui.components.color_picker import create_color_picker
import configs


def build_manage_passes_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Manage Passes tab content.

    Args:
        page:       Flet page reference
        state:      AppState (we use state.pass_state for data)
        api_client: APIClient for backend calls
    """
    ps = state.pass_state  # shorthand

    # ── Local mutable refs (UI-only) ──
    passes_json_editor = None
    passes_current_json = {}
    passes_current_class_type = None
    passes_dynamic_form = None
    passes_row_editor_ref = [None]
    passes_dynamic_text_modules = {} # To store dynamic fields for Generic passes
    apple_edit_refs = {} # For formatting Apple fields natively

    # ── UI Controls ──
    platform_ref = ft.Ref[ft.SegmentedButton]()
    action_button_ref = ft.Ref[ft.ElevatedButton]()
    
    def _get_selected_platform() -> str:
        if platform_ref.current and platform_ref.current.selected:
            return list(platform_ref.current.selected)[0]
        return "google"

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
    passes_json_container = ft.Container(
        content=ft.Text(state.t("msg.load_json_hint"), color="grey", size=11),
        expand=True,
    )
    passes_preview_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text(state.t("msg.preview_hint"), size=12, color="grey"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
    )
    passes_result_container = ft.Container(content=None)

    # ── Helpers ──

    def _set_status(msg, color="green"):
        passes_status.value = msg
        passes_status.color = color

    def update_ui_on_platform_change(e):
        passes_form_container.controls.clear()
        manage_passes_class_dropdown.value = None
        manage_passes_dropdown.value = None
        manage_passes_dropdown.options = []
        passes_result_container.content = None
        passes_preview_container.content = ft.Column(
            [
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text(state.t("msg.preview_hint"), size=12, color="grey"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        if _get_selected_platform() == "apple":
            if action_button_ref.current:
                action_button_ref.current.text = state.t("btn.open_apple_folder")
                action_button_ref.current.icon = "folder_open"
        else:
            if action_button_ref.current:
                action_button_ref.current.text = "Generate Save Link"
                action_button_ref.current.icon = "qr_code"
        load_passes_classes()
        page.update()

    # ── Business-logic handlers ──

    def startup_sync_passes():
        """Check local DB and sync passes from Google Wallet if empty."""
        try:
            passes = api_client.get_passes() if api_client else []
            if not passes or len(passes) == 0:
                _set_status(state.t("msg.syncing_google"), "blue")
                page.update()
                try:
                    api_client.sync_passes()
                    passes = api_client.get_passes() if api_client else []
                    if passes and len(passes) > 0:
                        _set_status(state.t("msg.found_passes", count=len(passes)))
                    else:
                        _set_status(state.t("msg.no_passes_found"), "orange")
                except Exception as sync_error:
                    _set_status(state.t("msg.error_syncing", error=str(sync_error)), "red")
                page.update()
        except Exception as e:
            _set_status(f"❌ Error checking local passes database: {e}", "red")
            page.update()

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
                
                # Preserve selection if still valid
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
            
            # Reset pass dropdown if no class selected
            if not manage_passes_class_dropdown.value:
                manage_passes_dropdown.options = []
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = "Select a class first"
            
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading classes: {e}", "red")
            page.update()

    def refresh_manage_passes():
        """Refresh logic for remote trigger."""
        load_passes_classes()
        # If a class is already selected, refresh the passes for that class too
        if manage_passes_class_dropdown.value:
            load_passes_for_class(manage_passes_class_dropdown.value)

    # Register this function for remote refresh
    state.register_refresh_callback("manage_passes_list", refresh_manage_passes)

    def load_passes_for_class(class_id: str):
        """Load passes for a specific class from local database."""
        _set_status("⏳ Fetching passes from local database...", "blue")
        page.update()
        try:
            platform = _get_selected_platform()
            if platform == "google":
                passes = api_client.get_passes_by_class(class_id) if api_client else []
            elif platform == "apple":
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
                        text=f"{str(p.get('object_id', '')).split('.')[-1]} ({p.get('holder_name', 'Unknown')})"
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
        """Handle class selection change in Manage Passes tab."""
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
        """Fetch and display pass for editing from local database."""
        nonlocal passes_json_editor, passes_current_json, passes_current_class_type, passes_dynamic_form

        if not manage_passes_dropdown.value:
            _set_status(state.t("msg.select_pass_err"), "red"); page.update(); return

        _set_status(state.t("msg.saving_local"), "blue"); page.update()

        try:
            object_id = manage_passes_dropdown.value
            platform = _get_selected_platform()
            
            if platform == "apple":
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
                    p_data_copy = p_data.copy()
                    pass_data = {}
                    
                    p_data_copy["holder_name"] = apple_edit_refs["holder_name"].current.value if "holder_name" in apple_edit_refs and apple_edit_refs["holder_name"].current else p_data.get("holder_name")

                    if apple_edit_refs.get("background_color") and apple_edit_refs["background_color"].current:
                         pass_data["hexBackgroundColor"] = apple_edit_refs["background_color"].current.value

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

                    if class_info and class_info.get("class_json"):
                        passes_preview_container.content = build_comprehensive_preview(class_info["class_json"], pass_data, state=state, platform="apple")
                    else:
                        passes_preview_container.content = ft.Text(state.t("msg.no_details"))
                    
                    if passes_json_editor:
                        passes_json_editor.update_json(p_data_copy)
                        
                    page.update()

                visual_data = p_data.get("visual_data", {})
                
                passes_form_container.controls.extend([
                    ft.Container(content=ft.Text(state.t("label.step_pass_holder"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5)),
                    _apple_field("holder_name", state.t("label.holder_name"), state.t("hint.john_doe"), p_data.get("holder_name", "")),
                    _apple_field("holder_email", state.t("label.holder_email"), state.t("hint.john_email"), p_data.get("holder_email", "")),

                    ft.Container(content=ft.Text(state.t("label.step_customize_color"), size=16, weight=ft.FontWeight.W_500, color="blue700"), padding=ft.padding.only(top=10, bottom=5))
                ])

                # Color Picker
                class AppleColorState:
                    def __init__(self, col): self.color = col
                    def get(self, k, default=None): return self.color if k == "background_color" else default
                    def update(self, k, v):
                        if k == "background_color": 
                            self.color = v
                            apple_edit_refs["background_color"] = ft.Ref()
                            apple_edit_refs["background_color"].current = type('obj', (object,), {'value' : v})
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

                passes_json_editor = JSONEditor(passes_current_json, state=state, read_only=True)
                passes_json_container.content = passes_json_editor.build()
                update_apple_preview()
                
                _set_status(state.t("msg.template_loaded"))
                page.update()
                return

            p_data = api_client.get_pass(object_id) if api_client else None
            if not p_data:
                _set_status(state.t("msg.template_not_found", id=object_id), "red"); page.update(); return

            passes_object_id_field.value = str(object_id).split('.')[-1]
            passes_object_id_field.data = object_id  # Store full ID in data for API calls
            class_id_raw = str(p_data.get("class_id",""))
            passes_class_id_field.value = class_id_raw.split('.')[-1]
            passes_class_id_field.data = class_id_raw

            class_info = api_client.get_class(p_data["class_id"])
            class_type = (
                (class_info.get("class_type") if class_info else None)
                or p_data.get("class_type", "Generic")
            )
            passes_current_class_type = class_type

            class_id_local = p_data.get("class_id", "")
            json_data = {
                "id": object_id,
                "classId": f"{configs.ISSUER_ID}.{class_id_local}",
                "holder_name": p_data.get("holder_name"),
                "holder_email": p_data.get("holder_email"),
                "status": p_data.get("status"),
            }

            if p_data.get("pass_data"):
                json_data.update(p_data["pass_data"])

            passes_current_json = json_data.copy()

            # Editable fields
            field_mappings = {
                #"id": {"label": "label.object_id", "type": "text", "read_only": True, "section": "Pass details"},
                #"classId": {"label": "label.class_id", "type": "text", "read_only": True, "section": "Pass details"},
                #{"name": "holder_name", "label": "label.holder_name", "type": "text", "hint": "e.g., https://example.com/logo.png", "section": "Header"},
                "holder_name": {"label": state.t("label.holder_name"), "type": "text", "section": "Pass details", "hide_label": True},
                "holder_email": {"label": state.t("label.email_req"), "type": "text", "section": "Pass details", "hide_label": True},
                "status": {"label": state.t("label.status"), "type": "select", "options": ["Active", "Completed", "Expired"], "section": "Status & notification", "hide_label": True},
                "messageType": {"label": state.t("label.notification_type"), "type": "select", "options": ["TEXT", "TEXT_AND_NOTIFY"], "section": "Status & notification", "hide_label": True},
            }

            if "messageType" not in json_data:
                json_data["messageType"] = "TEXT_AND_NOTIFY"
                passes_current_json["messageType"] = "TEXT_AND_NOTIFY"

            # IMPORTANT: text modules for passes are stored in relational tables and exposed by the API
            # as `textModulesData` at the top-level pass shape. Ensure we always carry them into the
            # editable JSON so the TextModuleRowEditor is pre-populated correctly.
            if p_data.get("textModulesData") and "textModulesData" not in passes_current_json:
                passes_current_json["textModulesData"] = p_data.get("textModulesData", [])

            # Event date/time from template
            template_event_date = None
            template_event_time = None
            if class_type == "EventTicket" and class_info and class_info.get("class_json"):
                class_json = class_info["class_json"]
                if "dateTime" in class_json:
                    date_time_obj = class_json.get("dateTime", {})
                    if "start" in date_time_obj:
                        start_datetime = date_time_obj.get("start", "")
                        if "T" in start_datetime:
                            template_event_date, template_event_time = start_datetime.split("T")
                            template_event_time = template_event_time.split(":")[0] + ":" + template_event_time.split(":")[1]

            if class_type == "EventTicket":
                if template_event_date:
                    json_data["event_date"] = template_event_date
                    passes_current_json["event_date"] = template_event_date
                if template_event_time:
                    json_data["event_time"] = template_event_time
                    passes_current_json["event_time"] = template_event_time

                field_mappings["event_date"] = {"label": state.t("label.event_date"), "type": "text", "read_only": True, "hide_label": True}
                field_mappings["event_time"] = {"label": state.t("label.event_time"), "type": "text", "read_only": True, "hide_label": True}

                pd = p_data.get("pass_data", {})
                passes_current_json["ticket_holder_name"] = str(pd.get("ticketHolderName", ""))
                field_mappings["ticket_holder_name"] = {"label": state.t("label.ticket_holder_name"), "type": "text", "hide_label": True}
                passes_current_json["confirmation_code"] = str(pd.get("confirmationCode", ""))
                field_mappings["confirmation_code"] = {"label": state.t("label.confirmation_code"), "type": "text", "hide_label": True}
                passes_current_json["seat"] = str(pd.get("seatNumber", ""))
                passes_current_json["section"] = str(pd.get("section", ""))
                passes_current_json["gate"] = str(pd.get("gate", ""))
                field_mappings["seat"] = {"label": state.t("label.seat"), "type": "text", "hide_label": True}
                field_mappings["section"] = {"label": state.t("label.section"), "type": "text", "hide_label": True}
                field_mappings["gate"] = {"label": state.t("label.gate"), "type": "text", "hide_label": True}

            elif class_type == "Generic":
                pd = p_data.get("pass_data", {})
                passes_current_json["issuer_name"] = str(pd.get("card_title", pd.get("issuer_name", "")))
                passes_current_json["header_value"] = str(pd.get("header_value", ""))
                passes_current_json["subheader_value"] = str(pd.get("subheader_value", ""))
                passes_current_json["logo_url"] = str(pd.get("logo_url", ""))
                passes_current_json["hero_image_url"] = str(pd.get("hero_image_url", ""))
                passes_current_json["hexBackgroundColor"] = str(pd.get("hexBackgroundColor", pd.get("hex_background_color", "")))
                
                # Setup basic notification preferences
                existing_messages = pd.get("messages", []) if isinstance(pd.get("messages"), list) else []
                if existing_messages:
                    first = existing_messages[0] or {}
                    inferred_message_type = first.get("messageType") or first.get("message_type")
                    if inferred_message_type:
                        passes_current_json["messageType"] = inferred_message_type
                        json_data["messageType"] = inferred_message_type
                
                # Setup dynamic fields for Generic
                field_mappings["logo_url"] = {"label": state.t("label.logo_url"), "type": "url", "hint": "https://example.com/logo.png", "section": "Header", "hide_label": True}
                field_mappings["hero_image_url"] = {"label": "Hero Image URL", "type": "url", "hint": "https://example.com/hero.png", "section": "Header", "hide_label": True}
                field_mappings["issuer_name"] = {"label": state.t("label.issuer_name"), "type": "text", "hint": "e.g., Your Business Name", "section": "Header", "hide_label": True}
                field_mappings["subheader_value"] = {"label": state.t("label.subheader"), "type": "text", "section": "Top Row", "hide_label": True}
                field_mappings["header_value"] = {"label": state.t("label.header_value"), "type": "text", "section": "Top Row", "hide_label": True}
                # hexBackgroundColor is handled via the color picker below, not as a form field
                # textModulesData is handled via the row editor below, not as a form field


            # Dynamic fields from pass_data
            if p_data.get("pass_data"):
                ignored_keys = {
                    "holder_name", "holder_email", "status", "id", "classId",
                    "event_date", "event_time", "messageType", "kind", "classReference",
                    "version", "hasUsers", "hasLinkedDevice", "smartTapRedemptionValue",
                    "state", "barcode", "messages", "locations", "reservationInfo",
                    "seatInfo", "ticketHolderName", "textModulesData", "linksModuleData",
                    "imageModulesData", "groupingInfo", "issuerId", "reviewStatus",
                    "confirmationCode", "seatNumber", "section", "gate",
                    "header_value", "subheader_value", "header", "subheader",
                    "issuer_name", "logo_url", "hero_image_url", "hexBackgroundColor",
                    "hex_background_color", "logo", "heroImage",
                    "barcode_type", "barcode_value", "card_title",
                }
                for key in p_data["pass_data"].keys():
                    if key not in ignored_keys:
                        field_mappings[key] = {"label": key.replace("_", " ").title(), "type": "text", "hide_label": True}

            def on_passes_form_change(updated_json):
                nonlocal passes_current_json
                passes_current_json = updated_json
                if passes_json_editor:
                    passes_json_editor.update_json(updated_json)
                
                # Create a preview copy with mapped fields
                preview_data = updated_json.copy()
                if "hero_image_url" in preview_data:
                    preview_data["hero_image"] = preview_data["hero_image_url"]
                if "issuer_name" in preview_data:
                    preview_data["card_title"] = preview_data["issuer_name"]

                if class_info and class_info.get("class_json"):
                    passes_preview_container.content = build_comprehensive_preview(class_info["class_json"], preview_data, state=state)
                else:
                    passes_preview_container.content = ft.Text(state.t("msg.no_details"))
                page.update()

            custom_section_controls = {}
            if class_type == "Generic":
                # Dynamic text module fields based on Template Blueprint
                class_rows = class_info.get("text_module_rows", []) if class_info else []
                pass_modules_list = passes_current_json.get("textModulesData", [])
                if not isinstance(pass_modules_list, list): pass_modules_list = []
                pass_modules = {m.get("id"): m for m in pass_modules_list}
                
                module_controls = []
                passes_dynamic_text_modules.clear()
                
                def create_on_mod_change(mid, h):
                    def on_mod_change(e):
                        nonlocal passes_current_json
                        if "textModulesData" not in passes_current_json:
                            passes_current_json["textModulesData"] = []
                        
                        found = False
                        for m in passes_current_json["textModulesData"]:
                            if m.get("id") == mid:
                                m["body"] = e.control.value
                                found = True
                                break
                        if not found:
                            passes_current_json["textModulesData"].append({"id": mid, "header": h, "body": e.control.value})
                        
                        on_passes_form_change(passes_current_json)
                    return on_mod_change

                for i, row in enumerate(class_rows):
                    row_controls = []
                    for pos in ["left", "middle", "right"]:
                        header = row.get(f"{pos}_header")
                        if header:
                            mod_id = f"row_{i}_{pos}"
                            existing_body = pass_modules.get(mod_id, {}).get("body", "")
                            
                            tf = ft.TextField(
                                hint_text=header, 
                                value=existing_body, 
                                on_change=create_on_mod_change(mod_id, header),
                                expand=True,
                                label=None
                            )
                            passes_dynamic_text_modules[mod_id] = tf
                            row_controls.append(tf)
                    
                    if row_controls:
                        module_controls.append(ft.Row(row_controls, spacing=10))

                # Color picker for Generic passes (same UX as Pass Generator)
                pass_color_state = {"background_color": passes_current_json.get("hexBackgroundColor", "#4285f4")}

                class PassColorState:
                    def __init__(self, initial_color, json_ref):
                        self.color = initial_color
                        self.json_ref = json_ref
                    def get(self, key, default=None):
                        if key == "background_color":
                            return self.color
                        return default
                    def update(self, key, value):
                        if key == "background_color":
                            self.color = value
                            self.json_ref["hexBackgroundColor"] = value
                            self.json_ref["hex_background_color"] = value

                color_state_obj = PassColorState(
                    passes_current_json.get("hexBackgroundColor", "#4285f4"),
                    passes_current_json,
                )

                def on_pass_color_change():
                    on_passes_form_change(passes_current_json)

                color_picker_widget = create_color_picker(page, color_state_obj, on_pass_color_change)
                
                # Use custom_section_controls to insert them in the middle
                custom_section_controls["Pass details"] = [
                    ft.Container(
                        content=ft.Text(state.t("label.section_modify_customized_card_color"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                        padding=ft.padding.only(top=10, bottom=5)
                    ),
                    color_picker_widget,
                    ft.Divider(height=10)
                ]
                
                custom_section_controls["Top Row"] = [
                    ft.Container(
                        content=ft.Text(state.t("label.section_information_rows"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                        padding=ft.padding.only(top=10, bottom=5)
                    ),
                    *module_controls,
                    ft.Divider(height=10)
                ]
                # No row editor needed here anymore
                passes_row_editor_ref[0] = None
            else:
                passes_row_editor_ref[0] = None

            passes_dynamic_form = DynamicForm(field_mappings, passes_current_json, state=state, on_change_callback=on_passes_form_change, custom_section_controls=custom_section_controls)

            passes_form_container.controls = passes_dynamic_form.build()

            passes_json_editor = JSONEditor(passes_current_json, state=state, read_only=True)
            passes_json_container.content = passes_json_editor.build()

            if class_info and class_info.get("class_json"):
                passes_preview_container.content = build_comprehensive_preview(class_info["class_json"], passes_current_json, state=state)
            else:
                passes_preview_container.content = ft.Text(state.t("msg.template_not_found", id=p_data.get("class_id")))

            _set_status(state.t("msg.template_loaded"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_and_sync_pass_handler(e):
        """Update pass locally AND sync to Google Wallet."""
        nonlocal passes_current_json, passes_dynamic_form

        if not passes_object_id_field.value:
            _set_status(state.t("msg.no_template_loaded"), "red"); page.update(); return

        platform = _get_selected_platform()
        
        if platform == "apple":
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
                
                # Fetch full data to generate new pkpass
                class_id = passes_class_id_field.data
                class_data = api_client.get_class(class_id)
                # Need pass_data with mapped custom fields...
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
            return

        _set_status("⏳ Updating and syncing to Google...", "blue"); page.update()

        try:
            object_id = passes_object_id_field.data
            # We use passes_current_json instead of dynamic_form.get_json_data() 
            # because the color picker updates passes_current_json directly,
            # and may not be synced to the form's internal state.
            form_data = passes_current_json.copy() if passes_current_json else {}

            holder_name = form_data.pop("holder_name", None)
            holder_email = form_data.pop("holder_email", None)
            status = form_data.pop("status", None)

            form_data.pop("id", None)
            form_data.pop("classId", None)
            # Remove helper UI fields that shouldn't go to API
            form_data.pop("event_date", None)
            form_data.pop("event_time", None)

            # Re-read textModulesData directly from components if Generic
            if passes_current_class_type == "Generic" and passes_dynamic_text_modules:
                form_data["textModulesData"] = [
                    {"id": mid, "header": tf.label if tf.label else tf.hint_text, "body": tf.value}
                    for mid, tf in passes_dynamic_text_modules.items()
                ]
            elif passes_row_editor_ref[0]:
                form_data["textModulesData"] = passes_row_editor_ref[0].get_rows() if hasattr(passes_row_editor_ref[0], 'get_rows') else form_data.get("textModulesData", [])

            # For Generic, convert the single editable message into the `messages` list
            # that our backend persists + syncs to Google Wallet.
            if passes_current_class_type == "Generic":
                msg_type = form_data.get("messageType") or "TEXT_AND_NOTIFY"
                msg_id = f"managed_{object_id}_0"
                form_data["messages"] = [{
                    "id": msg_id,
                    "header": "Update",
                    "body": "Your pass information has been updated.",
                    "messageType": msg_type,
                }]
                
                # Map UI field back to API expected field
                if "issuer_name" in form_data:
                    form_data["card_title"] = form_data.pop("issuer_name")

                if "hexBackgroundColor" in form_data:
                    form_data["hex_background_color"] = form_data["hexBackgroundColor"]
                        
            pass_data = form_data

            response = api_client.update_pass(
                object_id=object_id,
                holder_name=holder_name,
                holder_email=holder_email,
                status=status,
                pass_data=pass_data,
                sync_to_google=True,
            )
            _set_status("✅ " + response.get("message", "Pass updated and synced successfully!"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def sync_passes_manual(e):
        """Manual trigger for pass sync."""
        _set_status(state.t("msg.syncing_google"), "blue"); page.update()
        try:
            result = api_client.sync_passes()
            load_passes_classes()
            _set_status(f"✅ {result.get('message', 'Sync complete')}")
        except Exception as ex:
            _set_status(f"❌ Sync failed: {ex}", "red")
        page.update()

    def generate_save_link_handler(e):
        object_id = passes_object_id_field.data
        if not object_id:
            _set_status("❌ Please select a pass first", "red"); page.update()
            return

        platform = _get_selected_platform()
        if platform == "apple":
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
            return

        _set_status("⏳ Generating link...", "blue"); page.update()

        try:
            from core.qr_generator import generate_qr_code
            import time
            
            save_link = api_client.generate_save_link(object_id=object_id)
            if not save_link:
                
                raise Exception("Empty link retrieved from backend")
                
            qr_filename = f"pass_qr_{int(time.time())}"
            qr_image_path = generate_qr_code(save_link, qr_filename)
        
            passes_result_container.content = ft.Column([
                ft.Text("✅ Link generated successfully", color="green", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                # QR Code Section
                ft.Text(state.t("msg.pass_qr_scan") if hasattr(state, "t") else "Scan this QR code with your phone:", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                ft.Container(
                    content=ft.Image(src=qr_image_path, width=200, height=200, fit=ft.ImageFit.CONTAIN),
                    alignment=ft.alignment.center,
                    bgcolor="white",
                    border_radius=10,
                    padding=10
                ),
                ft.Text(state.t("msg.pass_qr_hint") if hasattr(state, "t") else "Scan with your camera app", size=10, color="grey", text_align=ft.TextAlign.CENTER),
                
                ft.Container(height=15),
                
                # Link Section
                ft.Text(state.t("label.or_use_link") if hasattr(state, "t") else "Or use this link directly:", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.TextField(value=save_link, read_only=True, expand=True, text_size=10),
                    ft.IconButton(icon="content_copy", tooltip=state.t("tooltip.copy_link") if hasattr(state, "t") else "Copy Link", on_click=lambda ev: page.set_clipboard(save_link))
                ]),
                ft.Container(height=5),
                ft.ElevatedButton(
                    state.t("btn.open_google_wallet") if hasattr(state, "t") else "Open Google Wallet",
                    icon="open_in_new",
                    on_click=lambda ev: page.launch_url(save_link),
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                ft.Container(height=10),
                ft.Text(f"Object ID: {object_id}", size=10, color="grey"),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            _set_status("✅ Link generated successfully", "green"); page.update()
            
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error generating link: {ex}", "red"); page.update()

    # ── Startup ──
    # startup_sync_passes() # Disabled per user request (keeps old test data off local DB)
    load_passes_classes()

    # Build UI Left Panel
    left_panel = ft.Container(
        width=420,
        content=ft.Column([
            ft.Text(state.t("header.manage_passes"), size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.manage_passes"), size=11, color="grey"),
            ft.Divider(),

            ft.Container(
                content=ft.SegmentedButton(
                    ref=platform_ref,
                    segments=[
                        ft.Segment(value="google", label=ft.Text("Google Wallet", weight=ft.FontWeight.BOLD)),
                        ft.Segment(value="apple", label=ft.Text("Apple Wallet", weight=ft.FontWeight.BOLD)),
                    ],
                    selected={"google"},
                    on_change=lambda e: update_ui_on_platform_change(e),
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=10, bottom=5),
            ),
            ft.Container(height=5),

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
                "Update & Sync to Google", icon="cloud_sync",
                on_click=update_and_sync_pass_handler, width=380,
                style=ft.ButtonStyle(bgcolor="blue", color="white"),
            ),
            ft.Container(height=10),
            ft.ElevatedButton(
                ref=action_button_ref,
                text="Generate Save Link", icon="qr_code",
                on_click=generate_save_link_handler, width=380,
                style=ft.ButtonStyle(bgcolor="green", color="white"),
            ),
            ft.Container(height=10),
            passes_result_container,
        ], spacing=8, scroll="auto"),
        padding=15, bgcolor="white",
    )

    # Splitter logic
    def on_pan_update(e: ft.DragUpdateEvent):
        new_width = left_panel.width + e.delta_x
        # Constrain width between 300 and 800 pixels
        left_panel.width = max(300, min(800, new_width))
        left_panel.update()

    splitter = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        drag_interval=10,
        on_pan_update=on_pan_update,
        content=ft.Container(width=5, bgcolor="transparent")
    )

    # ── 3-panel layout ──
    return ft.Container(
        content=ft.Row([
            # Left Panel
            left_panel,
            splitter,
            # Middle Panel: JSON Data
            ft.Container(
                width=320,
                content=ft.Column([
                    ft.Text(state.t("label.json_data"), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.live_json"), size=10, color="grey"),
                    ft.Container(height=10),
                    passes_json_container,
                ], scroll="auto"),
                padding=15, bgcolor="grey50",
            ),
            # Right Panel: Visual Preview
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text(state.t("label.visual_preview"), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.pass_look"), size=10, color="grey"),
                    ft.Container(height=20),
                    passes_preview_container,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, bgcolor="grey100",
            ),
        ], expand=True, spacing=0),
        expand=True,
    )
