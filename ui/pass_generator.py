"""
Pass Generator UI
Creates individual Google Wallet passes for end users
"""

import flet as ft
import os
import subprocess
import platform as platform_mod
from typing import Dict, List, Any, Optional
from core.qr_generator import generate_qr_code
from ui.components.text_module_row_editor import TextModuleRowEditor
from ui.components.preview_builder import build_comprehensive_preview
import configs
import string


# Field configurations for each pass type
PASS_TYPE_FIELDS = {
    "Generic": [
        {"name": "logo_url", "label": "label.logo_url", "type": "text", "hint": "e.g., https://example.com/logo.png", "section": "Header"},
        {"name": "hero_image_url", "label": "Hero Image URL", "type": "text", "hint": "e.g., https://example.com/hero.png", "section": "Header"},
        {"name": "card_title", "label": "label.issuer_name", "type": "text", "hint": "e.g., Your Business Name", "section": "Header"},
        {"name": "subheader_value", "label": "label.subheader_value", "type": "text", "hint": "e.g., VIP Level", "section": "Top Row"},
        {"name": "header_value", "label": "label.header_value", "type": "text", "hint": "e.g., VIP Member", "section": "Top Row"},
    ],
    "EventTicket": [
        {"name": "event_date", "label": "label.event_date", "type": "text", "hint": "e.g., 2024-12-25", "template_field": True},
        {"name": "event_time", "label": "label.event_time", "type": "text", "hint": "e.g., 19:00", "template_field": True},
        {"name": "seat_number", "label": "label.seat_number", "type": "text", "hint": "e.g., A12"},
        {"name": "section", "label": "label.section", "type": "text", "hint": "e.g., Lower Bowl"},
        {"name": "gate", "label": "label.gate", "type": "text", "hint": "e.g., Gate 3"},
    ],
    "LoyaltyCard": [
        {"name": "points_balance", "label": "label.points_balance", "type": "number", "hint": "e.g., 1500"},
        {"name": "tier_level", "label": "label.tier_level", "type": "text", "hint": "e.g., Gold"},
        {"name": "member_since", "label": "label.member_since", "type": "text", "hint": "e.g., 2024-01-15"},
        {"name": "rewards_available", "label": "label.rewards_available", "type": "number", "hint": "e.g., 3"},
    ],
    "GiftCard": [
        {"name": "balance", "label": "label.card_balance", "type": "number", "hint": "e.g., 50.00"},
        {"name": "card_number", "label": "label.card_number", "type": "text", "hint": "e.g., 1234-5678-9012"},
        {"name": "expiry_date", "label": "label.expiry_date", "type": "text", "hint": "e.g., 2025-12-31"},
    ],
    "TransitPass": [
        {"name": "pass_type", "label": "label.pass_type", "type": "text", "hint": "e.g., Monthly Pass"},
        {"name": "valid_from", "label": "label.valid_from", "type": "text", "hint": "e.g., 2024-12-01"},
        {"name": "valid_until", "label": "label.valid_until", "type": "text", "hint": "e.g., 2024-12-31"},
        {"name": "zones", "label": "label.zones", "type": "text", "hint": "e.g., Zone 1-3"},
    ],
}


def create_pass_generator(page: ft.Page, state, api_client, wallet_client):
    """
    Create the Pass Generator tab UI
    
    Args:
        page: Flet page instance
        api_client: API client for database operations
        wallet_client: Google Wallet client for pass generation
    """
    
    # Refs for form controls
    template_dropdown_ref = ft.Ref[ft.Dropdown]()
    holder_name_ref = ft.Ref[ft.TextField]()
    holder_email_ref = ft.Ref[ft.TextField]()
    message_type_ref = ft.Ref[ft.Dropdown]()  # For notification behavior
    platform_ref = ft.Ref[ft.SegmentedButton]()  # Target platform selector
    status_ref = ft.Ref[ft.Text]()
    result_container_ref = ft.Ref[ft.Container]()
    json_container_ref = ft.Ref[ft.Container]()

    # JSON editor state
    json_editor = None

    # Container for dynamic fields
    dynamic_fields_container = ft.Column(spacing=15)
    dynamic_field_refs = {}  # Store refs for dynamic fields
    pass_row_editor_ref = [None]  # List to hold reference mutably
    
    # Preview container
    preview_container = ft.Container(
        content=ft.Text(state.t("msg.pls_select_template"), color="grey"),
        alignment=ft.alignment.center,
        padding=20
    )
    
    # Current selected class data and custom color
    current_class_data = None
    custom_color_state = {"background_color": "#4285f4"}  # Default color
    
    # Color picker component (will be initialized after color change callback)
    color_picker_component = None
    color_picker_container = ft.Container(content=None)
    
    def _get_selected_platform() -> str:
        """Return 'google' or 'apple' from the SegmentedButton."""
        if platform_ref.current and platform_ref.current.selected:
            return list(platform_ref.current.selected)[0]
        return "google"

    def build_preview(class_data: Dict, pass_data: Dict) -> ft.Container:
        """Build visual pass preview from JSON data using centralized builder"""
        # Inject custom background color if set
        preview_class_data = class_data.copy()
        if custom_color_state.get("background_color"):
             preview_class_data["hexBackgroundColor"] = custom_color_state["background_color"]
        
        platform = _get_selected_platform()
        return build_comprehensive_preview(preview_class_data, pass_data, state=state, platform=platform)

    def update_ui_on_platform_change(e):
        """Called when the user switches between Google / Apple."""
        # Clear any previous result output
        if result_container_ref.current:
            result_container_ref.current.content = None
        # Rebuild form fields for the new platform
        build_form_fields()
        # Refresh the preview
        update_preview()
        page.update()
    
    def build_form_fields():
        """Clear and rebuild dynamic form fields based on current_class_data and platform."""
        if not current_class_data:
            return

        platform = _get_selected_platform()
        class_type = current_class_data.get("class_type", "Generic")

        # Clear existing dynamic fields
        dynamic_fields_container.controls.clear()
        dynamic_field_refs.clear()

        if platform == "apple":
            dynamic_field_refs["apple_holder_name"] = holder_name_ref
            dynamic_field_refs["apple_holder_email"] = holder_email_ref

            dynamic_fields_container.controls.extend([
                ft.Container(
                    content=ft.Text(state.t("label.step_pass_holder"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                    padding=ft.padding.only(top=10, bottom=5)
                ),
                ft.TextField(
                    ref=holder_name_ref,
                    label=state.t("label.name_req") if state.t("label.name_req") != "label.name_req" else "Holder Name",
                    hint_text=state.t("hint.john_doe"),
                    width=380,
                    on_change=lambda e: update_preview()
                ),
                ft.TextField(
                    ref=holder_email_ref,
                    label=state.t("label.email_req") if state.t("label.email_req") != "label.email_req" else "Holder Email",
                    hint_text=state.t("hint.john_email"),
                    width=380
                ),
                ft.Container(
                    content=ft.Text(state.t("label.step_customize_color"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                    padding=ft.padding.only(top=10, bottom=5)
                ),
                color_picker_container,
                ft.Container(
                    content=ft.Text(state.t("label.step_pass_details"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                    padding=ft.padding.only(top=10, bottom=5)
                )
            ])

            for f_name, f_label, f_hint in [
                ("apple_org_name", state.t("label.organization_name"), state.t("hint.my_company")),
                ("apple_logo_text", state.t("label.logo_text"), state.t("hint.pass")),
                ("apple_logo_url", state.t("label.logo_icon_url"), state.t("hint.logo_url")),
                ("apple_strip_url", state.t("label.strip_hero_image_url"), state.t("hint.strip_url"))
            ]:
                f_ref = ft.Ref[ft.TextField]()
                dynamic_field_refs[f_name] = f_ref
                dynamic_fields_container.controls.append(
                    ft.TextField(
                        ref=f_ref,
                        label=f_label,
                        hint_text=f_hint,
                        width=380,
                        on_change=lambda e: update_preview()
                    )
                )

            dynamic_fields_container.controls.append(
                ft.Container(
                    content=ft.Text(state.t("label.step_top_row"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                    padding=ft.padding.only(top=10, bottom=5)
                )
            )
            _add_apple_field_pair("apple_header", dynamic_fields_container, state.t("label.step_top_row"))

            dynamic_fields_container.controls.append(
                ft.Container(
                    content=ft.Text(state.t("label.step_info_rows"), size=16, weight=ft.FontWeight.W_500, color="blue700"),
                    padding=ft.padding.only(top=10, bottom=5)
                )
            )
            dynamic_fields_container.controls.append(ft.Text(state.t("label.primary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _add_apple_field_pair("apple_primary", dynamic_fields_container, state.t("label.primary_field"))
            dynamic_fields_container.controls.append(ft.Text(state.t("label.secondary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _add_apple_field_pair("apple_sec", dynamic_fields_container, state.t("label.secondary_field"))
            dynamic_fields_container.controls.append(ft.Text(state.t("label.auxiliary_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _add_apple_field_pair("apple_aux", dynamic_fields_container, state.t("label.auxiliary_field"))
            dynamic_fields_container.controls.append(ft.Text(state.t("label.back_field"), size=12, weight=ft.FontWeight.W_500, color="grey700"))
            _add_apple_field_pair("apple_back", dynamic_fields_container, state.t("label.back_field"))
            
            pass_row_editor_ref[0] = None

        elif platform == "google":
            # Pass Holder Info
            dynamic_fields_container.controls.extend([
                ft.Container(
                    content=ft.Text(state.t("label.pass_holder_info") if state.t("label.pass_holder_info") != "label.pass_holder_info" else "Pass Holder Information", size=16, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(top=10, bottom=5)
                ),
                ft.TextField(
                    ref=holder_name_ref,
                    label=state.t("label.name_req") if state.t("label.name_req") != "label.name_req" else "Holder Name",
                    hint_text="e.g., John Doe",
                    width=380,
                    on_change=lambda e: update_preview()
                ),
                ft.TextField(
                    ref=holder_email_ref,
                    label=state.t("label.email_req") if state.t("label.email_req") != "label.email_req" else "Holder Email",
                    hint_text="e.g., john@example.com",
                    width=380
                ),
                ft.Container(height=5),
                ft.Dropdown(
                    ref=message_type_ref,
                    label=state.t("label.notification_type") if state.t("label.notification_type") != "label.notification_type" else "Notification Type",
                    hint_text=state.t("label.notification_type") if state.t("label.notification_type") != "label.notification_type" else "Notification Type",
                    width=380,
                    value="TEXT_AND_NOTIFY",
                    options=[
                        ft.dropdown.Option(key="TEXT", text=state.t("option.notification_none") if state.t("option.notification_none") != "option.notification_none" else "No Notification"),
                        ft.dropdown.Option(key="TEXT_AND_NOTIFY", text=state.t("option.notification_push") if state.t("option.notification_push") != "option.notification_push" else "Send Push Notification"),
                    ]
                ),
                ft.Container(height=10),
                ft.Column([
                    ft.Text(state.t("label.customize_color") if state.t("label.customize_color") != "label.customize_color" else "Customize Color", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(state.t("subtitle.choose_color") if state.t("subtitle.choose_color") != "subtitle.choose_color" else "Choose a custom color", size=10, color="grey"),
                    color_picker_container
                ]),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text(state.t("label.pass_details") if state.t("label.pass_details") != "label.pass_details" else "Pass Details", size=16, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(top=10, bottom=5)
                )
            ])

            # -----------------------------------------------------------
            # Common fields (from PASS_TYPE_FIELDS)
            # -----------------------------------------------------------
            fields_config = PASS_TYPE_FIELDS.get(class_type, [])
            current_section = None
            for field_config in fields_config:
                if "section" in field_config and field_config["section"] != current_section:
                    current_section = field_config["section"]
                    dynamic_fields_container.controls.append(
                        ft.Container(
                            content=ft.Text(current_section, size=16, weight=ft.FontWeight.W_500, color="blue700"),
                            padding=ft.padding.only(top=10, bottom=5)
                        )
                    )

                field_ref = ft.Ref[ft.TextField]()
                dynamic_field_refs[field_config["name"]] = field_ref

                # Pre-populate template fields with values from class
                initial_value = ""
                is_readonly = False
                if class_type == "Generic":
                    logo_url = current_class_data.get("logo_url")
                    card_title = current_class_data.get("card_title")
                    header_text = current_class_data.get("header_text")
                    if field_config["name"] == "logo_url" and logo_url:
                        initial_value = logo_url
                    elif field_config["name"] == "hero_image_url" and current_class_data.get("hero_image_url"):
                        initial_value = current_class_data.get("hero_image_url")
                    elif field_config["name"] == "card_title" and card_title:
                        initial_value = card_title
                    elif field_config["name"] == "header_value" and header_text:
                        initial_value = header_text

                if field_config.get("template_field", False):
                    is_readonly = True
                    class_json = current_class_data.get("class_json", {})
                    dt_obj = class_json.get("dateTime", {})
                    start_dt = dt_obj.get("start", "")
                    if "T" in start_dt:
                        t_date, t_time = start_dt.split("T")
                        t_time = t_time[:5]
                    else:
                        t_date = t_time = ""
                    if field_config["name"] == "event_date" and t_date:
                        initial_value = t_date
                    elif field_config["name"] == "event_time" and t_time:
                        initial_value = t_time

                field = ft.TextField(
                    ref=field_ref,
                    label=state.t(field_config["label"]) if state.t(field_config["label"]) != field_config["label"] else field_config["label"].replace("label.", "").replace("_", " ").title(),
                    hint_text=field_config["hint"],
                    value=initial_value,
                    read_only=is_readonly,
                    width=380,
                    on_change=lambda e: update_preview()
                )
                dynamic_fields_container.controls.append(field)

            # -----------------------------------------------------------
            # Platform-specific information fields (Generic only)
            # -----------------------------------------------------------
            if class_type == "Generic":
                pass_row_editor_ref[0] = None

                template_rows = current_class_data.get("text_module_rows", [])
                if template_rows:
                    dynamic_fields_container.controls.append(
                        ft.Container(
                            content=ft.Text("Information Fields", size=16, weight=ft.FontWeight.W_500, color="blue700"),
                            padding=ft.padding.only(top=10, bottom=5)
                        )
                    )
                    for row in template_rows:
                        row_idx = row.get("row_index", 0)
                        fields_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.START)

                        def _add_google_field(col_name, header_key, parent_row, _row_idx=row_idx):
                            header_text = row.get(header_key)
                            if header_text:
                                fid = f"row_{_row_idx}_{col_name}"
                                fref = ft.Ref[ft.TextField]()
                                dynamic_field_refs[fid] = fref
                                parent_row.controls.append(
                                    ft.TextField(
                                        ref=fref,
                                        label=header_text,
                                        hint_text=f"Enter {header_text}",
                                        expand=True,
                                        on_change=lambda e: update_preview()
                                    )
                                )

                        _add_google_field("left", "left_header", fields_row)
                        _add_google_field("middle", "middle_header", fields_row)
                        _add_google_field("right", "right_header", fields_row)

                        if fields_row.controls:
                            dynamic_fields_container.controls.append(
                                ft.Container(content=fields_row, padding=ft.padding.only(bottom=5))
                            )
            else:
                pass_row_editor_ref[0] = None

    def _add_apple_field_pair(prefix: str, container, header_name: str = "Top Row"):
        """Add a Label + Value row for an Apple StoreCard field."""
        label_ref = ft.Ref[ft.TextField]()
        value_ref = ft.Ref[ft.TextField]()
        dynamic_field_refs[f"{prefix}_label"] = label_ref
        dynamic_field_refs[f"{prefix}_value"] = value_ref

        container.controls.append(
            ft.Row([
                ft.TextField(
                    ref=label_ref,
                    label=state.t("label.field_label"),
                    hint_text=state.t("hint.dynamic_label", header=header_name),
                    expand=True,
                    on_change=lambda e: update_preview()
                ),
                ft.TextField(
                    ref=value_ref,
                    label=state.t("label.field_value"),
                    hint_text=state.t("hint.dynamic_value", header=header_name),
                    expand=True,
                    on_change=lambda e: update_preview()
                ),
            ], spacing=10)
        )

    def _collect_text_modules() -> list:
        """Collect textModulesData from dynamic fields, aware of the current platform."""
        platform = _get_selected_platform()
        text_modules: list = []

        if platform == "google":
            # Google: iterate template rows (row_X_left/middle/right)
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
                        if val:
                            text_modules.append({"id": field_id, "header": header_text, "body": val})

        elif platform == "apple":
            apple_slots = [
                "apple_primary",
                "apple_sec",
                "apple_aux",
                "apple_back",
            ]
            for slot in apple_slots:
                lbl_key = f"{slot}_label"
                val_key = f"{slot}_value"
                if lbl_key in dynamic_field_refs and val_key in dynamic_field_refs:
                    lbl_ref = dynamic_field_refs[lbl_key]
                    val_ref = dynamic_field_refs[val_key]
                    lbl = lbl_ref.current.value if lbl_ref.current else ""
                    val = val_ref.current.value if val_ref.current else ""
                    if lbl or val:
                        text_modules.append({"id": slot, "header": lbl or "", "body": val or ""})

        return text_modules


    def on_color_change():
        """Handle color change from color picker"""
        update_preview()
    
    def update_preview():
        """Update preview based on current form values"""
        nonlocal json_editor
        if not current_class_data: # Use the top-level current_class_data
            return

        # Collect pass data from form
        pass_data = {
            "holder_name": holder_name_ref.current.value if holder_name_ref.current else "John Doe",
        }

        # Inject background color
        if custom_color_state.get("background_color"):
             pass_data["hexBackgroundColor"] = custom_color_state["background_color"]

        # Add dynamic field values
        for field_name, field_ref in dynamic_field_refs.items():
            if field_ref.current:
                val = field_ref.current.value or ""
                pass_data[field_name] = val
                
                # Direct mappings for preview builder
                if field_name == "logo_url":
                    pass_data["logo_url"] = val
                elif field_name == "hero_image_url":
                    pass_data["hero_image"] = val
                elif field_name == "card_title":
                    pass_data["card_title"] = val

        # Handle Generic Text Modules (platform-aware)
        class_type = current_class_data.get("class_type", "Generic")
        if class_type == "Generic":
            text_modules_data = _collect_text_modules()
            if text_modules_data:
                pass_data["textModulesData"] = text_modules_data

        # Update visual preview
        preview_container.content = build_preview(current_class_data, pass_data)

        # Update JSON panel
        if json_container_ref.current:
            import json
            from ui.components.json_editor import JSONEditor
            display_json = {**current_class_data, **pass_data}
            json_editor = JSONEditor(display_json, state=state, on_change=None, read_only=True)
            json_container_ref.current.content = json_editor.build()

        page.update()
    
    def on_template_selected(e):
        """Handle template selection"""
        if not template_dropdown_ref.current.value:
            return
        
        try:
            # Get class_id
            class_id = template_dropdown_ref.current.value
            
            # Get class data from local database
            nonlocal current_class_data
            if class_id in class_metadata:
                class_data = class_metadata[class_id]
            else:
                # Fetch from database if not in metadata
                class_data = api_client.get_class(class_id) if api_client else None
                
                if not class_data:
                    status_ref.current.value = state.t("msg.template_not_found", id=class_id)
                    status_ref.current.color = "red"
                    page.update()
                    return
                
                # Store in metadata
                class_metadata[class_id] = class_data
            
            current_class_data = class_data # Update the top-level current_class_data
            
            # Get class type
            class_type = class_data.get("class_type", "Generic")
            
            # Extract visual properties from class_json if available
            class_json = class_data.get("class_json", {})
            
            # Extract background color
            base_color = class_data.get("base_color") or class_json.get("hexBackgroundColor", "#4285f4")
            
            # Extract logo URL
            logo_url = class_data.get("logo_url")
            if not logo_url and "logo" in class_json:
                logo_url = class_json.get("logo", {}).get("sourceUri", {}).get("uri")
            elif not logo_url and "programLogo" in class_json:
                logo_url = class_json.get("programLogo", {}).get("sourceUri", {}).get("uri")
            
            # Extract header text
            header_text = class_data.get("header_text") or class_data.get("issuer_name", state.t("placeholder.business_name"))
            if not header_text or header_text == state.t("placeholder.business_name"):
                if "localizedIssuerName" in class_json:
                    header_text = class_json.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
                elif "issuerName" in class_json:
                    header_text = class_json.get("issuerName", "Business")
            
            # Extract card title
            card_title = class_data.get("card_title", state.t("placeholder.pass_title"))
            if not card_title or card_title == state.t("placeholder.pass_title"):
                if "localizedProgramName" in class_json:
                    card_title = class_json.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
                elif "eventName" in class_json:
                    card_title = class_json.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
                elif "cardTitle" in class_json:
                    card_title = class_json.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")
            
            # Extract event date and time from template (for EventTicket)
            template_event_date = None
            template_event_time = None
            if class_type == "EventTicket" and "dateTime" in class_json:
                date_time_obj = class_json.get("dateTime", {})
                # Check for start date/time
                if "start" in date_time_obj:
                    start_datetime = date_time_obj.get("start", "")
                    # Format: "2024-12-25T19:00:00" -> split into date and time
                    if "T" in start_datetime:
                        template_event_date, template_event_time = start_datetime.split("T")
                        template_event_time = template_event_time.split(":")[0] + ":" + template_event_time.split(":")[1]  # HH:MM
            
            # Store current class data for preview
            current_class_data.update({ # Update the existing dictionary
                "class_type": class_type,
                "class_id": class_id,
                "base_color": base_color,
                "logo_url": logo_url,
                "header_text": header_text,
                "card_title": card_title
            })
            
            # Initialize custom color with template color
            custom_color_state["background_color"] = base_color
            
            # Create/update color picker with the template's base color
            nonlocal color_picker_component
            
            # Create a simple state object that mimics template_state interface
            class SimpleColorState:
                def __init__(self, initial_color, on_change_callback):
                    self.color = initial_color
                    self.on_change = on_change_callback
                
                def get(self, key, default=None):
                    if key == "background_color":
                        return self.color
                    return default
                
                def update(self, key, value):
                    if key == "background_color":
                        self.color = value
                        custom_color_state["background_color"] = value
                        if self.on_change:
                            self.on_change()
            
            color_state = SimpleColorState(base_color, on_color_change)
            
            # Import and use the function-based color picker
            from ui.components.color_picker import create_color_picker
            color_picker_component = create_color_picker(page, color_state, on_color_change)
            color_picker_container.content = color_picker_component
            
            # Build form fields for the current platform
            build_form_fields()
            
            status_ref.current.value = state.t("msg.loaded_template_type", type=class_type)
            status_ref.current.color = "green"
            
            # Update preview
            update_preview()
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            status_ref.current.value = f"❌ Error: {str(ex)}"
            status_ref.current.color = "red"
        
        page.update()
    
    # Store class metadata (id -> full class info)
    class_metadata = {}
    
    def load_templates():
        """Load available templates into dropdown from local database"""
        try:
            # Fetch classes from local database via API
            classes = api_client.get_classes() if api_client else []
            
            if classes and len(classes) > 0:
                # Clear metadata
                class_metadata.clear()
                
                # Store metadata for each class
                for cls in classes:
                    class_metadata[cls["class_id"]] = cls
                
                template_dropdown_ref.current.options = [
                    ft.dropdown.Option(
                        key=cls["class_id"],
                        text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})"
                    )
                    for cls in classes
                ]
                status_ref.current.value = state.t("msg.loaded_classes", count=len(classes))
                status_ref.current.color = "green"
            else:
                template_dropdown_ref.current.options = []
                status_ref.current.value = state.t("msg.no_templates")
                status_ref.current.color = "blue"
            page.update()
        except Exception as e:
            status_ref.current.value = f"❌ Error loading templates: {e}"
            status_ref.current.color = "red"
    # Register this function for remote refresh
    state.register_refresh_callback("pass_generator_templates", load_templates)
    
    def _open_folder(folder_path):
        """Open a folder in the OS file manager."""
        try:
            if platform_mod.system() == "Windows":
                os.startfile(folder_path)
            elif platform_mod.system() == "Darwin":
                subprocess.call(["open", folder_path])
            else:
                subprocess.call(["xdg-open", folder_path])
        except Exception as exc:
            print(f"Warning: Could not open folder: {exc}")

    def generate_pass(e):
        """Generate the pass for the selected platform."""
        # Validate inputs
        if not template_dropdown_ref.current.value:
            status_ref.current.value = state.t("msg.pls_select_template")
            status_ref.current.color = "red"
            page.update()
            return
        
        if not holder_name_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_name")
            status_ref.current.color = "red"
            page.update()
            return
        
        if not holder_email_ref.current.value:
            status_ref.current.value = state.t("msg.pls_enter_email")
            status_ref.current.color = "red"
            page.update()
            return
        
        # Determine target platform
        platform = _get_selected_platform()  # "google" or "apple"
        
        status_ref.current.value = "⏳ Generating pass..."
        status_ref.current.color = "blue"
        page.update()
        
        try:
            # Collect pass data
            pass_data = {}
            for field_name, field_ref in dynamic_field_refs.items():
                if field_ref.current and field_ref.current.value:
                    pass_data[field_name] = field_ref.current.value
            
            # Ensure background color is included in pass_data for local DB persistence
            custom_color = custom_color_state.get("background_color")
            if custom_color:
                pass_data["hexBackgroundColor"] = custom_color
            
            # Add text module rows dynamically (platform-aware)
            class_type = current_class_data.get("class_type", "Generic")
            if class_type == "Generic":
                text_modules_data = _collect_text_modules()
                if text_modules_data:
                    pass_data["textModulesData"] = text_modules_data

            # Generate unique object ID
            import time
            import configs
            timestamp = int(time.time())
            clean_name = holder_name_ref.current.value.replace(' ', '_').lower()
            object_suffix = f"pass_{timestamp}_{clean_name}"
            object_id = f"{configs.ISSUER_ID}.{object_suffix}"
            
            # Get class_id and ensure it has issuer prefix
            class_id = template_dropdown_ref.current.value
            if not class_id.startswith(configs.ISSUER_ID):
                class_id = f"{configs.ISSUER_ID}.{class_id}"
            
            # Get class type from current class data
            class_type = current_class_data.get("class_type", "Generic")
            
            # Get custom color from state
            custom_color = custom_color_state.get("background_color")
            
            # Get message type from dropdown
            message_type = message_type_ref.current.value if message_type_ref.current else "TEXT_AND_NOTIFY"
            
            # For Generic, we create a minimal object and encode notification behavior
            # as an explicit `messages` entry (so it gets persisted to local DB too).
            if class_type == "Generic":
                msg_id = f"create_msg_{timestamp}"
                pass_data["messages"] = [{
                    "id": msg_id,
                    "header": "Welcome",
                    "body": "Your pass has been created",
                    "messageType": message_type,
                }]

            # ==============================================================
            # GOOGLE WALLET GENERATION
            # ==============================================================
            if platform == "google":
                status_ref.current.value = state.t("msg.creating_in_google")
                status_ref.current.color = "blue"
                page.update()

                # Build the appropriate pass object for Google Wallet
                if class_type == "EventTicket":
                    google_pass_object = wallet_client.build_event_ticket_object(
                        object_id=object_id,
                        class_id=class_id,
                        holder_name=holder_name_ref.current.value,
                        holder_email=holder_email_ref.current.value,
                        pass_data=pass_data,
                        custom_color=custom_color,
                        message_type=message_type
                    )
                elif class_type == "LoyaltyCard":
                    google_pass_object = wallet_client.build_loyalty_object(
                        object_id=object_id,
                        class_id=class_id,
                        holder_name=holder_name_ref.current.value,
                        holder_email=holder_email_ref.current.value,
                        pass_data=pass_data,
                        custom_color=custom_color,
                        message_type=message_type
                    )
                else:
                    google_pass_object = wallet_client.build_generic_object(
                        object_id=object_id,
                        class_id=class_id,
                        holder_name=holder_name_ref.current.value,
                        holder_email=holder_email_ref.current.value,
                        pass_data=pass_data,
                        custom_color=custom_color,
                        message_type=None
                    )
                
                # Create pass object in Google Wallet
                wallet_result = wallet_client.create_pass_object(google_pass_object, class_type)
                
                # Generate JWT-signed save link
                save_link = wallet_client.generate_save_link(object_id, class_type, class_id)
                
                # Try to create pass in local database (optional)
                db_saved = False
                try:
                    status_ref.current.value = state.t("msg.saving_local")
                    status_ref.current.color = "blue"
                    page.update()
                    
                    db_class_id = class_id.split('.')[-1] if '.' in class_id else class_id
                    db_result = api_client.create_pass(
                        object_id=object_id,
                        class_id=db_class_id,
                        holder_name=holder_name_ref.current.value,
                        holder_email=holder_email_ref.current.value,
                        status="Active",
                        pass_data=pass_data
                    )
                    db_saved = True
                    if state:
                        state.refresh_ui("manage_passes_list")
                        state.refresh_ui("send_notification_list")
                except Exception as db_error:
                    print(f"Warning: Could not save to local database: {db_error}")
                
                # Generate QR code
                status_ref.current.value = "⏳ Generating QR code..."
                status_ref.current.color = "blue"
                page.update()
                
                qr_filename = f"pass_qr_{int(time.time())}"
                qr_image_path = generate_qr_code(save_link, qr_filename)
                
                # Show Google result
                result_container_ref.current.content = ft.Column([
                    ft.Text(state.t("status.pass_generated_google"), color="green", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    ft.Text(
                        f"{state.t('msg.saved_local_db') if db_saved else state.t('msg.not_saved_local_db')}",
                        size=10,
                        color="green" if db_saved else "orange"
                    ),
                    ft.Container(height=15),
                    ft.Text(state.t("msg.pass_qr_scan"), size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    ft.Container(
                        content=ft.Image(src=qr_image_path, width=200, height=200, fit=ft.ImageFit.CONTAIN),
                        alignment=ft.alignment.center,
                        bgcolor="white",
                        border_radius=10,
                        padding=10
                    ),
                    ft.Text(state.t("msg.pass_qr_hint"), size=10, color="grey", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=15),
                    ft.Text(state.t("label.or_use_link"), size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.TextField(value=save_link, read_only=True, expand=True, text_size=10),
                        ft.IconButton(icon="content_copy", tooltip=state.t("tooltip.copy_link"), on_click=lambda e: page.set_clipboard(save_link))
                    ]),
                    ft.Container(height=5),
                    ft.ElevatedButton(
                        state.t("btn.open_google_wallet"),
                        icon="open_in_new",
                        on_click=lambda e: page.launch_url(save_link),
                        style=ft.ButtonStyle(bgcolor="blue", color="white")
                    ),
                    ft.Container(height=10),
                    ft.Text(f"Object ID: {object_id}", size=10, color="grey"),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                
                status_ref.current.value = state.t("status.pass_generated_google")
                status_ref.current.color = "green"

            # ==============================================================
            # APPLE WALLET GENERATION
            # ==============================================================
            elif platform == "apple":
                status_ref.current.value = "⏳ Generating Apple Wallet pass..."
                status_ref.current.color = "blue"
                page.update()

                from services.apple_wallet_service import AppleWalletService
                apple_service = AppleWalletService()

                apple_pass_path = apple_service.create_pass(
                    class_data=current_class_data,
                    pass_data=pass_data,
                    object_id=object_id,
                )

                apple_folder = os.path.dirname(apple_pass_path)
                
                # Generate a secure random token for APNs
                import secrets
                auth_token = secrets.token_hex(16)
                
                # Call the API client to save the pass to the database
                def safe_field(label_ref, value_ref, key_name):
                    if label_ref in dynamic_field_refs and value_ref in dynamic_field_refs:
                        if dynamic_field_refs[label_ref].current and dynamic_field_refs[value_ref].current:
                            l = dynamic_field_refs[label_ref].current.value
                            v = dynamic_field_refs[value_ref].current.value
                            if l and v:
                                return [{"key": key_name, "label": l, "value": v}]
                    return []

                def get_val(key):
                    if key in dynamic_field_refs and dynamic_field_refs[key].current:
                        val = dynamic_field_refs[key].current.value
                        return val if val else None
                    return None

                store_card_data = {
                    "background_color": custom_color_state.get("background_color"),
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

                db_saved = False
                try:
                    db_class_id = class_id.split('.')[-1] if '.' in class_id else class_id
                    api_client.create_apple_pass(
                        serial_number=object_id, # Using object_id as Apple serial_number
                        class_id=db_class_id,
                        pass_type_id=configs.APPLE_PASS_TYPE_ID,
                        holder_name=holder_name_ref.current.value if holder_name_ref.current else "Apple Holder",
                        holder_email=holder_email_ref.current.value if holder_email_ref.current else "apple@example.com",
                        auth_token=auth_token,
                        pass_data=pass_data,
                        store_card_data=store_card_data
                    )
                    db_saved = True
                    if state:
                        state.refresh_ui("manage_passes_list")
                except Exception as db_error:
                    print(f"Warning: Could not save Apple pass to local database: {db_error}")

                result_container_ref.current.content = ft.Column([
                    ft.Text("✅ Apple Pass Generated Successfully!", color="green", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    ft.Text(f"Saved at: {apple_pass_path}", size=10, color="grey", selectable=True),
                    ft.Text(
                        f"{state.t('msg.saved_local_db') if db_saved else state.t('msg.not_saved_local_db')}",
                        size=10,
                        color="green" if db_saved else "orange"
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        text=state.t("btn.open_apple_folder"),
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda e, folder=apple_folder: _open_folder(folder),
                        style=ft.ButtonStyle(bgcolor="black", color="white")
                    ),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                
                status_ref.current.value = "✅ Apple Wallet pass generated!"
                status_ref.current.color = "green"
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            status_ref.current.value = f"❌ Error: {str(ex)}"
            status_ref.current.color = "red"
            result_container_ref.current.content = None
        
        page.update()
    
    # Build UI
    left_panel = ft.Container(
        width=420,
        content=ft.Column([
            ft.Text(state.t("header.pass_generator"), size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.pass_generator"), size=11, color="grey"),
            ft.Divider(),

            # ── Platform Selector (SegmentedButton) ──
            ft.Container(
                content=ft.SegmentedButton(
                    ref=platform_ref,
                    segments=[
                        ft.Segment(value="google", label=ft.Text("Google Wallet", weight=ft.FontWeight.BOLD)),
                        ft.Segment(value="apple", label=ft.Text("Apple Wallet", weight=ft.FontWeight.BOLD)),
                    ],
                    selected={"google"},
                    on_change=update_ui_on_platform_change,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=10, bottom=5),
            ),

            ft.Container(height=5),

            ft.Text(state.t("label.select_template"), size=16, weight=ft.FontWeight.BOLD),
            ft.Dropdown(
                ref=template_dropdown_ref,
                label=state.t("label.class_id"),
                hint_text=state.t("label.select_class_err"),
                width=380,
                on_change=on_template_selected
            ),

            ft.Container(height=10),

            dynamic_fields_container,

            ft.Divider(height=20),

            ft.ElevatedButton(
                state.t("btn.generate_pass"),
                icon="add_card",
                on_click=generate_pass,
                width=380,
                style=ft.ButtonStyle(bgcolor="blue", color="white")
            ),

            ft.Container(height=10),

            ft.Text(ref=status_ref, value="", size=12),

            ft.Container(height=10),

            ft.Container(ref=result_container_ref, content=None)

        ], spacing=10, scroll="auto"),
        padding=15,
        bgcolor="white"
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

    ui = ft.Row([
        # Left Panel: Form
        left_panel,
        splitter,

        # Middle Panel: JSON Data
        ft.Container(
            width=320,
            content=ft.Column([
                ft.Text(state.t("label.json_data"), size=18, weight=ft.FontWeight.BOLD),
                ft.Text(state.t("subtitle.live_json"), size=10, color="grey"),
                ft.Container(height=10),
                ft.Container(
                    ref=json_container_ref,
                    content=ft.Text(state.t("msg.pls_select_template"), color="grey", size=11),
                    expand=True
                )
            ], scroll="auto"),
            padding=15,
            bgcolor="grey50"
        ),

        # Right Panel: Visual Preview
        ft.Container(
            expand=True,
            content=ft.Column([
                ft.Text(state.t("label.visual_preview"), size=18, weight=ft.FontWeight.BOLD),
                ft.Text(state.t("subtitle.pass_look"), size=10, color="grey"),
                ft.Container(height=20),
                preview_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
            padding=15,
            bgcolor="grey100"
        )
    ], expand=True, spacing=0)
    
    # Load templates after UI is created
    load_templates()
    
    return ui
