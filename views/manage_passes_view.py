"""
Manage Passes View
Extracted from main.py — 3-panel layout for managing individual Google Wallet pass objects.
"""

import flet as ft
from ui.components.json_editor import JSONEditor
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
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

    # ── UI Controls ──
    manage_passes_class_dropdown = ft.Dropdown(
        label="Select Class",
        hint_text="Choose a class first",
        width=400,
        options=[],
    )

    manage_passes_dropdown = ft.Dropdown(
        label="Select Pass Object",
        hint_text="Select a class first",
        width=400,
        options=[],
    )

    passes_status = ft.Text("", size=12)

    passes_object_id_field = ft.TextField(
        label="Object ID", width=400, read_only=True, bgcolor="grey100"
    )
    passes_class_id_field = ft.TextField(
        label="Class ID", width=400, read_only=True, bgcolor="grey100"
    )

    passes_form_container = ft.Column(
        controls=[ft.Text("Load a pass to see editable fields", color="grey", size=11)],
        spacing=8,
        scroll="auto",
    )
    passes_json_container = ft.Container(
        content=ft.Text("Load a pass to see JSON", color="grey", size=11),
        expand=True,
    )
    passes_preview_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon("credit_card", size=80, color="grey300"),
                ft.Text("Preview will appear here", size=12, color="grey"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
    )

    # ── Helpers ──

    def _set_status(msg, color="green"):
        passes_status.value = msg
        passes_status.color = color

    def build_manage_preview(class_data: dict) -> ft.Container:
        """Build visual pass preview (identical to manage templates preview)."""
        bg_color = class_data.get("hexBackgroundColor") or class_data.get("base_color", "#4285f4")

        logo_url = None
        if "programLogo" in class_data:
            logo_url = class_data.get("programLogo", {}).get("sourceUri", {}).get("uri")
        elif "logo" in class_data:
            logo_url = class_data.get("logo", {}).get("sourceUri", {}).get("uri")
        elif "logo_url" in class_data:
            logo_url = class_data.get("logo_url")

        hero_url = None
        if "heroImage" in class_data:
            hero_url = class_data.get("heroImage", {}).get("sourceUri", {}).get("uri")

        header_text = "Business Name"
        card_title = "Pass Title"

        if "localizedIssuerName" in class_data:
            header_text = class_data.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", "Business")
        elif "issuerName" in class_data:
            header_text = class_data.get("issuerName", "Business")
        elif "issuer_name" in class_data:
            header_text = class_data.get("issuer_name", "Business")

        if "localizedProgramName" in class_data:
            card_title = class_data.get("localizedProgramName", {}).get("defaultValue", {}).get("value", "Program")
        elif "eventName" in class_data:
            card_title = class_data.get("eventName", {}).get("defaultValue", {}).get("value", "Event")
        elif "header" in class_data:
            header_text = class_data.get("header", {}).get("defaultValue", {}).get("value", "Header")
        if "cardTitle" in class_data:
            card_title = class_data.get("cardTitle", {}).get("defaultValue", {}).get("value", "Title")
        elif "card_title" in class_data:
            card_title = class_data.get("card_title", "Title")

        if logo_url:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(src=logo_url, width=50, height=50, fit=ft.ImageFit.COVER),
            )
        else:
            logo_control = ft.Container(
                width=50, height=50, border_radius=25, bgcolor="white30",
                content=ft.Icon("business", color="white", size=30),
                alignment=ft.alignment.center,
            )

        if hero_url:
            hero_control = ft.Container(
                height=150,
                content=ft.Image(src=hero_url, width=300, height=150, fit=ft.ImageFit.COVER),
            )
        else:
            hero_control = ft.Container(
                height=150, bgcolor="black12",
                content=ft.Column(
                    [ft.Icon("image", size=40, color="grey"), ft.Text("Hero Image", size=12, color="grey")],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        return ft.Container(
            width=300, bgcolor=bg_color, border_radius=15,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=15, color="black26", offset=ft.Offset(0, 5)),
            content=ft.Column([
                ft.Container(padding=15, content=ft.Row([
                    logo_control, ft.Container(width=10),
                    ft.Text(header_text, color="white", weight=ft.FontWeight.BOLD, size=14, expand=True),
                ])),
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(card_title, color="white", size=20, weight=ft.FontWeight.BOLD),
                ),
                hero_control,
                ft.Container(bgcolor="white", padding=15, content=ft.Column([
                    ft.Text("Pass Details", color="grey", size=11),
                    ft.Container(height=5),
                    ft.Row([
                        ft.Container(width=70, height=70, bgcolor="grey200", border_radius=5,
                                     content=ft.Icon("qr_code_2", size=50, color="grey"),
                                     alignment=ft.alignment.center),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text("Sample User", weight=ft.FontWeight.BOLD, size=13, color="black"),
                            ft.Text("ID: 1234567890", size=11, color="grey"),
                        ]),
                    ]),
                ])),
            ], spacing=0),
        )

    # ── Business-logic handlers ──

    def startup_sync_passes():
        """Check local DB and sync passes from Google Wallet if empty."""
        try:
            passes = api_client.get_passes() if api_client else []
            if not passes or len(passes) == 0:
                _set_status("⏳ Syncing passes from Google Wallet...", "blue")
                page.update()
                try:
                    api_client.sync_passes()
                    passes = api_client.get_passes() if api_client else []
                    if passes and len(passes) > 0:
                        _set_status(f"✅ Synced {len(passes)} passes from Google Wallet")
                    else:
                        _set_status("ℹ️ No passes found in Google Wallet (or sync failed silently)", "orange")
                except Exception as sync_error:
                    _set_status(f"❌ Error syncing passes: {sync_error}", "red")
                page.update()
        except Exception as e:
            _set_status(f"❌ Error checking local passes database: {e}", "red")
            page.update()

    def load_passes_classes():
        """Load classes into the Manage Passes class dropdown."""
        try:
            classes = api_client.get_classes() if api_client else []
            if classes and len(classes) > 0:
                manage_passes_class_dropdown.options = [
                    ft.dropdown.Option(key=cls["class_id"], text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})")
                    for cls in classes
                ]
                manage_passes_class_dropdown.value = None
                manage_passes_class_dropdown.hint_text = "Choose a class"
                _set_status(f"✅ Loaded {len(classes)} class(es). Select a class to see its passes.")
            else:
                manage_passes_class_dropdown.options = []
                manage_passes_class_dropdown.value = None
                manage_passes_class_dropdown.hint_text = "No classes available"
                _set_status("ℹ️ No classes found. Create one in 'Template Builder' tab.", "blue")
            manage_passes_dropdown.options = []
            manage_passes_dropdown.value = None
            manage_passes_dropdown.hint_text = "Select a class first"
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading classes: {e}", "red")
            page.update()

    def load_passes_for_class(class_id: str):
        """Load passes for a specific class from local database."""
        _set_status("⏳ Fetching passes from local database...", "blue")
        page.update()
        try:
            passes = api_client.get_passes_by_class(class_id) if api_client else []
            if passes and len(passes) > 0:
                manage_passes_dropdown.options = [
                    ft.dropdown.Option(key=p["object_id"], text=f"{p['object_id']} ({p.get('holder_name', 'Unknown')})")
                    for p in passes
                ]
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = "Choose a pass"
                _set_status(f"✅ {len(passes)} pass(es) found for this class.")
            else:
                manage_passes_dropdown.options = []
                manage_passes_dropdown.value = None
                manage_passes_dropdown.hint_text = "No passes for this class"
                _set_status("ℹ️ No passes found for this class.", "blue")
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
            _set_status("❌ Please select a pass", "red"); page.update(); return

        _set_status("⏳ Loading pass from local database...", "blue"); page.update()

        try:
            object_id = manage_passes_dropdown.value
            p_data = api_client.get_pass(object_id) if api_client else None
            if not p_data:
                _set_status(f"❌ Pass '{object_id}' not found in database", "red"); page.update(); return

            passes_object_id_field.value = object_id
            passes_class_id_field.value = p_data.get("class_id")

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
                "holder_name": {"label": "Holder Name", "type": "text"},
                "holder_email": {"label": "Holder Email", "type": "text"},
                "status": {"label": "Status", "type": "select", "options": ["Active", "Completed", "Expired"]},
                "messageType": {"label": "Message Type", "type": "select", "options": ["TEXT", "TEXT_AND_NOTIFY"]},
            }

            if "messageType" not in json_data:
                json_data["messageType"] = "TEXT_AND_NOTIFY"
                passes_current_json["messageType"] = "TEXT_AND_NOTIFY"

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

                field_mappings["event_date"] = {"label": "Event Date", "type": "text", "read_only": True}
                field_mappings["event_time"] = {"label": "Event Time", "type": "text", "read_only": True}

                pd = p_data.get("pass_data", {})
                passes_current_json["ticket_holder_name"] = str(pd.get("ticketHolderName", ""))
                field_mappings["ticket_holder_name"] = {"label": "Ticket Holder Name", "type": "text"}
                passes_current_json["confirmation_code"] = str(pd.get("confirmationCode", ""))
                field_mappings["confirmation_code"] = {"label": "Confirmation Code", "type": "text"}
                passes_current_json["seat"] = str(pd.get("seatNumber", ""))
                passes_current_json["section"] = str(pd.get("section", ""))
                passes_current_json["gate"] = str(pd.get("gate", ""))
                field_mappings["seat"] = {"label": "Seat", "type": "text"}
                field_mappings["section"] = {"label": "Section", "type": "text"}
                field_mappings["gate"] = {"label": "Gate", "type": "text"}

            elif class_type == "Generic":
                pd = p_data.get("pass_data", {})
                passes_current_json["header_value"] = str(pd.get("header_value", ""))
                passes_current_json["subheader_value"] = str(pd.get("subheader_value", ""))
                field_mappings["header_value"] = {"label": "Header Value", "type": "text"}
                field_mappings["subheader_value"] = {"label": "Subheader Value", "type": "text"}

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
                }
                for key in p_data["pass_data"].keys():
                    if key not in ignored_keys:
                        field_mappings[key] = {"label": key.replace("_", " ").title(), "type": "text"}

            def on_passes_form_change(updated_json):
                nonlocal passes_current_json
                passes_current_json = updated_json
                if passes_json_editor:
                    passes_json_editor.update_json(updated_json)
                if class_info and class_info.get("class_json"):
                    passes_preview_container.content = build_manage_preview(class_info["class_json"])
                else:
                    passes_preview_container.content = ft.Text("No preview available")
                page.update()

            custom_form_controls = []
            if class_type == "Generic":
                def on_pass_rows_change(modules):
                    nonlocal passes_current_json
                    passes_current_json["textModulesData"] = modules
                    on_passes_form_change(passes_current_json)

                # Initialize from existing pass data if any
                initial_pass_rows = passes_current_json.get("textModulesData", [])
                row_editor = TextModuleRowEditor(initial_pass_rows, on_change=on_pass_rows_change, mode="pass")
                passes_row_editor_ref[0] = row_editor
                
                custom_form_controls.append(ft.Divider())
                custom_form_controls.append(row_editor)
            else:
                passes_row_editor_ref[0] = None

            passes_dynamic_form = DynamicForm(field_mappings, passes_current_json, on_passes_form_change, custom_controls=custom_form_controls)
            passes_form_container.controls = passes_dynamic_form.build()

            passes_json_editor = JSONEditor(passes_current_json, read_only=True)
            passes_json_container.content = passes_json_editor.build()

            if class_info and class_info.get("class_json"):
                passes_preview_container.content = build_manage_preview(class_info["class_json"])
            else:
                passes_preview_container.content = ft.Text("Class info not found for preview")

            _set_status("✅ Pass loaded from Google Wallet. Edit fields and click 'Update Pass' to save.")
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_pass_object_handler(e):
        """Update pass locally (without syncing to Google Wallet immediately)."""
        nonlocal passes_current_json, passes_dynamic_form

        if not passes_object_id_field.value:
            _set_status("❌ No pass loaded", "red"); page.update(); return

        _set_status("⏳ Saving pass to local database...", "blue"); page.update()

        try:
            object_id = passes_object_id_field.value
            form_data = passes_dynamic_form.get_json_data() if passes_dynamic_form else {}

            holder_name = form_data.pop("holder_name", None)
            holder_email = form_data.pop("holder_email", None)
            status = form_data.pop("status", None)

            form_data.pop("id", None)
            form_data.pop("classId", None)
            form_data.pop("event_date", None)
            form_data.pop("event_time", None)

            # Re-read textModulesData directly from component if Generic, or rely on pass_data
            if passes_current_class_type == "Generic" and passes_row_editor_ref[0]:
                form_data["textModulesData"] = passes_row_editor_ref[0].get_rows() if hasattr(passes_row_editor_ref[0], 'get_rows') else form_data.get("textModulesData", [])

            pass_data = form_data

            response = api_client.update_pass(
                object_id=object_id,
                holder_name=holder_name,
                holder_email=holder_email,
                status=status,
                pass_data=pass_data,
                sync_to_google=False,
            )
            _set_status(response.get("message", "✅ Pass updated locally successfully!"))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def push_to_google_wallet_handler(e):
        """Push the current pass state to Google Wallet."""
        if not passes_object_id_field.value:
            _set_status("❌ No pass loaded", "red"); page.update(); return

        _set_status("⏳ Pushing pass to Google Wallet...", "blue"); page.update()
        try:
            response = api_client.push_pass_to_google(object_id=passes_object_id_field.value)
            _set_status(response.get("message", "✅ Pass pushed to Google Wallet successfully!"))
        except Exception as ex:
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def sync_passes_manual(e):
        """Manual trigger for pass sync."""
        _set_status("⏳ Syncing passes from Google Wallet...", "blue"); page.update()
        try:
            result = api_client.sync_passes()
            load_passes_classes()
            _set_status(f"✅ {result.get('message', 'Sync complete')}")
        except Exception as ex:
            _set_status(f"❌ Sync failed: {ex}", "red")
        page.update()

    # ── Startup ──
    startup_sync_passes()
    load_passes_classes()

    # Build UI Left Panel
    left_panel = ft.Container(
        width=420,
        content=ft.Column([
            ft.Text("Manage Pass Objects", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Select, preview, and edit your pass objects", size=11, color="grey"),
            ft.Divider(),
            ft.Row([
                ft.IconButton("sync", on_click=sync_passes_manual, tooltip="Refresh passes from Google Wallet"),
                ft.Text("Sync from Google Wallet", size=11, color="grey"),
            ]),
            ft.Container(height=5),
            ft.Text("1. Select Class", size=13, weight=ft.FontWeight.W_500, color="blue700"),
            manage_passes_class_dropdown,
            ft.Container(height=5),
            ft.Text("2. Select Pass", size=13, weight=ft.FontWeight.W_500, color="blue700"),
            manage_passes_dropdown,
            ft.ElevatedButton(
                "Load Pass", icon="download", on_click=show_pass, width=380,
                style=ft.ButtonStyle(bgcolor="green", color="white"),
            ),
            passes_status,
            ft.Divider(height=20),
            ft.Text("Pass Details", size=16, weight=ft.FontWeight.BOLD),
            passes_object_id_field,
            passes_class_id_field,
            ft.Container(height=5),
            ft.Text("Editable Fields", size=14, weight=ft.FontWeight.W_500, color="grey700"),
            passes_form_container,
            ft.Divider(height=20),
            ft.ElevatedButton(
                "Save to Local DB", icon="save",
                on_click=update_pass_object_handler, width=380,
                style=ft.ButtonStyle(bgcolor="orange", color="white"),
            ),
            ft.Container(height=10),
            ft.ElevatedButton(
                "Update in Google Wallet API", icon="cloud_upload",
                on_click=push_to_google_wallet_handler, width=380,
                style=ft.ButtonStyle(bgcolor="blue", color="white"),
            ),
            ft.Container(height=10),
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
                    ft.Text("JSON Data", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Complete pass JSON", size=10, color="grey"),
                    ft.Container(height=10),
                    passes_json_container,
                ], scroll="auto"),
                padding=15, bgcolor="grey50",
            ),
            # Right Panel: Visual Preview
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text("Visual Preview", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("How your pass will look", size=10, color="grey"),
                    ft.Container(height=20),
                    passes_preview_container,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, bgcolor="grey100",
            ),
        ], expand=True, spacing=0),
        expand=True,
    )
