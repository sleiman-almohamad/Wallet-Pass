import flet as ft
from ui.theme import PRIMARY, TEXT_PRIMARY, TEXT_MUTED, CARD_BG, card, section_title
from ui.components.color_picker import create_color_picker
from ui.components.mobile_mockup import MobileMockupPreview
import configs
import time
import httpx

def build_google_manage_passes_view(page: ft.Page, state, api_client, preview: MobileMockupPreview) -> ft.Container:
    """
    Build the Manage Passes tab content for Google Wallet.
    """
    # ── State ──
    current_pass_json = {}
    current_class_info = None
    dynamic_field_refs: dict = {}
    dynamic_text_modules: dict = {}

    # ── Refs for core fields ──
    holder_name_ref = ft.Ref[ft.TextField]()
    holder_email_ref = ft.Ref[ft.TextField]()
    status_ref = ft.Ref[ft.Dropdown]()
    message_type_ref = ft.Ref[ft.Dropdown]()

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

    custom_color_state = {"background_color": "#4285f4"}
    bg_color_picker_container = ft.Container(content=None)

    def _sync_preview():
        if not current_pass_json:
            return
        
        # Prepare data for mockup
        preview_data = current_pass_json.copy()
        
        # Sync from refs
        if holder_name_ref.current:
            preview_data["holder_name"] = holder_name_ref.current.value
        if holder_email_ref.current:
            preview_data["holder_email"] = holder_email_ref.current.value
            
        # Sync from dynamic refs
        for fid, fref in dynamic_field_refs.items():
            if fref.current:
                val = fref.current.value
                preview_data[fid] = val
                # Mockup specific mapping
                if fid == "logo_url":   preview_data["logo_url"] = val
                if fid == "hero_image": preview_data["hero_image"] = val
                if fid == "card_title": preview_data["card_title"] = val
                if fid == "header":     preview_data["header"] = val
                if fid == "subheader":  preview_data["subheader"] = val

        # Sync text modules
        if dynamic_text_modules:
            preview_data["textModulesData"] = [
                {"id": mid, "header": tf.current.label if tf.current.label else tf.current.hint_text, "body": tf.current.value}
                for mid, tf in dynamic_text_modules.items()
                if tf.current and tf.current.value
            ]

        preview_data["bg_color"] = custom_color_state.get("background_color", "#4285f4")
        preview.update_data(preview_data, "google")

    def _on_color_change():
        _sync_preview()

    color_state_obj = SimpleColorState(custom_color_state, _on_color_change)
    bg_color_picker_container.content = create_color_picker(page, color_state_obj, _on_color_change, "background_color", "Background Color")

    # ── UI Selection Controls ──
    class_dropdown = ft.Dropdown(
        label="Select Template (Class ID)",
        hint_text="Choose a template...",
        width=400, border_radius=8, text_size=13,
        options=[],
    )

    pass_dropdown = ft.Dropdown(
        label="Select Pass",
        hint_text="Choose a pass...",
        width=400, border_radius=8, text_size=13,
        options=[],
        visible=False
    )

    status_text = ft.Text("", size=12)
    edit_form = ft.Column(visible=False, spacing=15)

    # ── File Picker Logic ──
    current_picker_target = None
    
    def on_file_result(e: ft.FilePickerResultEvent):
        nonlocal current_picker_target
        if e.files and current_picker_target:
            file = e.files[0]
            try:
                # Get the API base URL
                api_url = getattr(configs, "API_BASE_URL", "http://localhost:8000")
                upload_endpoint = f"{api_url}/upload/image"
                
                with open(file.path, "rb") as f:
                    files = {"file": (file.name, f)}
                    response = httpx.post(upload_endpoint, files=files)
                    
                if response.status_code == 200:
                    uploaded_url = response.json().get("url")
                    current_picker_target.value = uploaded_url
                    current_picker_target.update()
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

    # ── Data Loading ──
    def load_classes():
        try:
            classes = api_client.get_classes() if api_client else []
            if classes:
                class_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(cls.get("class_id", "")),
                        text=f"{str(cls.get('class_id', '')).split('.')[-1]} ({cls.get('class_type', 'Unknown')})"
                    )
                    for cls in classes if cls.get("class_id")
                ]
                class_dropdown.hint_text = "Choose a template..."
            else:
                class_dropdown.options = []
                class_dropdown.hint_text = "No templates found."
        except Exception as e:
            status_text.value = f"❌ Error loading classes: {e}"
            status_text.color = "red"
        if class_dropdown.page:
            class_dropdown.update()

    def load_passes_for_class(class_id: str):
        try:
            status_text.value = "⏳ Loading passes..."
            status_text.color = "blue"
            if status_text.page: status_text.update()
            
            passes = api_client.get_passes_by_class(class_id) if api_client else []
            if passes:
                pass_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(p.get("object_id", "")),
                        text=p.get("holder_name", "Unknown")
                    )
                    for p in passes if p.get("object_id")
                ]
                pass_dropdown.hint_text = f"Found {len(passes)} passes. Select one."
                status_text.value = ""
            else:
                pass_dropdown.options = []
                pass_dropdown.hint_text = "No passes found for this template."
                status_text.value = "No passes found locally."
        except Exception as e:
            status_text.value = f"❌ Error loading passes: {e}"
            status_text.color = "red"
        
        pass_dropdown.value = None
        if pass_dropdown.page: pass_dropdown.update()
        if status_text.page: status_text.update()

    # ── Event Handlers ──
    def on_class_change(e):
        if class_dropdown.value:
            pass_dropdown.visible = True
            edit_form.visible = False
            load_passes_for_class(class_dropdown.value)
        else:
            pass_dropdown.visible = False
            edit_form.visible = False
        page.update()

    def on_pass_change(e):
        nonlocal current_pass_json, current_class_info
        if not pass_dropdown.value:
            edit_form.visible = False
            page.update()
            return

        try:
            object_id = pass_dropdown.value
            p_data = api_client.get_pass(object_id)
            if not p_data:
                return

            current_class_info = api_client.get_class(p_data["class_id"])
            
            current_pass_json = {
                "id": object_id,
                "classId": p_data.get("class_id"),
                "holder_name": p_data.get("holder_name"),
                "holder_email": p_data.get("holder_email"),
                "status": p_data.get("status", "Active"),
            }
            if p_data.get("pass_data"):
                current_pass_json.update(p_data["pass_data"])

            # Setup Color
            hex_bg = current_pass_json.get("hexBackgroundColor", current_pass_json.get("hex_background_color", "#4285f4"))
            custom_color_state["background_color"] = hex_bg

            _build_pass_edit_form(p_data, current_class_info)
            edit_form.visible = True
            
            # Initial sync
            _sync_preview()
        except Exception as ex:
            import traceback; traceback.print_exc()
            status_text.value = f"❌ Error loading pass: {ex}"
            status_text.color = "red"
        page.update()

    def reset_form(e=None):
        """Reset selections and hide the edit form."""
        class_dropdown.value = None
        pass_dropdown.value = None
        pass_dropdown.visible = False
        edit_form.visible = False
        status_text.value = ""
        preview.update_data({"bg_color": "#4285f4"}, "google")
        page.update()

    def _build_pass_edit_form(pass_obj, class_info):
        class_type = class_info.get("class_type", "Generic")
        dynamic_field_refs.clear()
        dynamic_text_modules.clear()

        # Holder Info Section
        holder_controls = [
            section_title("Pass Holder Info", ft.Icons.PERSON),
            ft.Row([
                ft.TextField(ref=holder_name_ref, label="Holder Name", value=pass_obj.get("holder_name", ""),
                             expand=1, border_radius=8, text_size=13, on_change=lambda e: _sync_preview()),
                ft.TextField(ref=holder_email_ref, label="Holder Email", value=pass_obj.get("holder_email", ""),
                             expand=1, border_radius=8, text_size=13, on_change=lambda e: _sync_preview()),
            ], spacing=12),
            ft.Row([
                ft.Dropdown(
                    ref=status_ref, label="Status", value=pass_obj.get("status", "Active"),
                    expand=1, border_radius=8, text_size=13,
                    options=[
                        ft.dropdown.Option("Active"),
                        ft.dropdown.Option("Completed"),
                        ft.dropdown.Option("Expired"),
                    ]
                ),
                ft.Dropdown(
                    ref=message_type_ref, label="Notification Type", 
                    value=pass_obj.get("pass_data", {}).get("messageType", "TEXT_AND_NOTIFY"),
                    expand=1, border_radius=8, text_size=13,
                    options=[
                        ft.dropdown.Option("TEXT", "No Notification"),
                        ft.dropdown.Option("TEXT_AND_NOTIFY", "Send Push Notification"),
                    ]
                ),
            ], spacing=12),
        ]

        # Colors Section
        colors_controls = [
            section_title("Customize Color", ft.Icons.PALETTE),
            bg_color_picker_container,
        ]

        # Pass Details Section
        details_controls = [section_title("Pass Details", ft.Icons.DESCRIPTION)]
        pd = pass_obj.get("pass_data", {})

        def _add_detail_field(label, key, value, hint="", read_only=False, multiline=False):
            fref = ft.Ref[ft.TextField]()
            dynamic_field_refs[key] = fref
            
            tf = ft.TextField(
                ref=fref, label=label, value=str(value or ""), hint_text=hint,
                read_only=read_only, border_radius=8, text_size=13,
                expand=True,
                multiline=multiline,
                min_lines=3 if multiline else 1,
                max_lines=10 if multiline else 1,
                on_change=lambda e: _sync_preview()
            )
            
            # If it's an image field, add upload button
            is_image_field = "url" in key.lower() or "image" in key.lower()
            if is_image_field and not read_only:
                details_controls.append(ft.Row([
                    tf,
                    ft.IconButton(
                        icon=ft.Icons.IMAGE_SEARCH_ROUNDED,
                        tooltip=f"Select {label}",
                        on_click=lambda e, target=tf: pick_image_for(target)
                    )
                ], spacing=5))
            else:
                details_controls.append(tf)

        if class_type == "Generic":
             _add_detail_field("Issuer Name", "card_title", pd.get("card_title", pd.get("issuer_name", "")), "e.g., My Studio")
             _add_detail_field("Header", "header", pd.get("header_value", ""), "e.g., Welcome")
             _add_detail_field("Subheader", "subheader", pd.get("subheader_value", ""), "e.g., Special Guest")
             _add_detail_field("Logo URL", "logo_url", pd.get("logo_url", ""), "https://...")
             _add_detail_field("Hero Image URL", "hero_image", pd.get("hero_image_url",pd.get("heroImage", "")), "https://...")
        elif class_type == "EventTicket":
             _add_detail_field("Ticket Holder", "ticketHolderName", pd.get("ticketHolderName", ""), "Name on ticket")
             _add_detail_field("Confirmation Code", "confirmationCode", pd.get("confirmationCode", ""), "ABC-123")
             _add_detail_field("Seat", "seatNumber", pd.get("seatNumber", ""), "A-12")
             _add_detail_field("Section", "section", pd.get("section", ""), "Lower Bowl")
             _add_detail_field("Gate", "gate", pd.get("gate", ""), "Gate 5")

        # Info Fields (Text Modules)
        info_section = None
        if class_type == "Generic":
            class_rows = class_info.get("text_module_rows", [])
            pass_modules_list = pd.get("textModulesData", [])
            pass_modules = {m.get("id"): m for m in pass_modules_list} if isinstance(pass_modules_list, list) else {}

            if class_rows:
                info_controls = [section_title("Information Fields", ft.Icons.TABLE_ROWS)]
                for i, row in enumerate(class_rows):
                    row_controls = []
                    for pos in ["left", "middle", "right"]:
                        hdr = row.get(f"{pos}_header")
                        if hdr:
                            mid = f"row_{i}_{pos}"
                            existing_body = pass_modules.get(mid, {}).get("body", "")
                            fref = ft.Ref[ft.TextField]()
                            dynamic_text_modules[mid] = fref
                            row_controls.append(ft.TextField(
                                ref=fref, label=hdr, value=existing_body,
                                expand=True, border_radius=8, text_size=13,
                                multiline=True, min_lines=3, max_lines=10,
                                on_change=lambda e: _sync_preview()
                            ))
                    if row_controls:
                        info_controls.append(ft.Row(row_controls, spacing=8))
                info_section = card(ft.Column(info_controls, spacing=8))

        # Bottom Buttons
        action_controls = [
            ft.Container(height=10),
            ft.ElevatedButton(
                "Update & Sync to Google", icon=ft.Icons.CLOUD_SYNC, height=48,
                on_click=save_updates_handler, width=380,
                style=ft.ButtonStyle(bgcolor=PRIMARY, color="white", 
                                     shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            ft.Container(height=5),
            ft.ElevatedButton(
                "Generate Save Link", icon=ft.Icons.QR_CODE, height=48,
                on_click=generate_save_link_handler, width=380,
                style=ft.ButtonStyle(bgcolor="green", color="white",
                                     shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            ft.Container(height=10),
            ft.Container(height=10),
            status_text,
        ]

        edit_form.controls = [
            card(ft.Column(holder_controls, spacing=8)),
            card(ft.Column(colors_controls, spacing=8)),
            card(ft.Column(details_controls, spacing=8)),
        ]
        if info_section:
            edit_form.controls.append(info_section)
        
        edit_form.controls.extend(action_controls)

    def save_updates_handler(e):
        if not pass_dropdown.value: return
        
        status_text.value = "⏳ Updating..."
        status_text.color = "blue"
        page.update()

        try:
            object_id = pass_dropdown.value
            
            # Prepare pass_data
            form_pd = {}
            for fid, fref in dynamic_field_refs.items():
                if fref.current:
                    # Map back to Google field names
                    if fid == "logo_url":   form_pd["logo_url"] = fref.current.value
                    elif fid == "hero_image": form_pd["hero_image_url"] = fref.current.value
                    elif fid == "card_title": form_pd["card_title"] = fref.current.value
                    elif fid == "header":     form_pd["header_value"] = fref.current.value
                    elif fid == "subheader":  form_pd["subheader_value"] = fref.current.value
                    else: form_pd[fid] = fref.current.value

            form_pd["hexBackgroundColor"] = custom_color_state["background_color"]
            form_pd["hex_background_color"] = custom_color_state["background_color"]
            
            if dynamic_text_modules:
                form_pd["textModulesData"] = [
                    {"id": mid, "header": tf.current.label if tf.current.label else tf.current.hint_text, "body": tf.current.value}
                    for mid, tf in dynamic_text_modules.items()
                    if tf.current and tf.current.value
                ]

            # Sync push message if Generic
            status_val = status_ref.current.value
            msg_type = message_type_ref.current.value
            if current_class_info.get("class_type") == "Generic":
                form_pd["messages"] = [{
                    "id": f"upd_{int(time.time())}",
                    "header": "Pass Update",
                    "body": "Your pass information has been updated.",
                    "messageType": msg_type or "TEXT_AND_NOTIFY",
                }]

            response = api_client.update_pass(
                object_id=object_id,
                holder_name=holder_name_ref.current.value,
                holder_email=holder_email_ref.current.value,
                status=status_val,
                pass_data=form_pd,
                sync_to_google=True
            )
            # --- Success Dialog ---
            def dialog_dismissed(e):
                reset_form()

            def close_dlg(e):
                page.close(upd_dlg)

            upd_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Pass Updated Successfully!", weight=ft.FontWeight.BOLD),
                content=ft.Text(response.get("message", "The pass has been updated and synced to Google Wallet."), size=13),
                on_dismiss=dialog_dismissed,
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(upd_dlg)

            status_text.value = "✅ Pass updated"
            status_text.color = "green"
        except Exception as ex:
            status_text.value = f"❌ Error: {ex}"
            status_text.color = "red"
        page.update()

    def generate_save_link_handler(e):
        if not pass_dropdown.value: return
        status_text.value = "⏳ Generating link..."
        status_text.color = "blue"
        page.update()
        try:
            from core.qr_generator import generate_qr_code
            object_id = pass_dropdown.value
            save_link = api_client.generate_save_link(object_id=object_id)
            qr_filename = f"pass_qr_{int(time.time())}"
            qr_image_path = generate_qr_code(save_link, qr_filename)
        
            # --- Success Dialog ---
            def dialog_dismissed(e):
                reset_form()

            def close_dlg(e):
                page.close(qr_dlg)

            qr_dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("✅ Save Link Generated", weight=ft.FontWeight.BOLD),
                content=ft.Column([
                    ft.Text("Scan to Save", weight=ft.FontWeight.BOLD, size=16),
                    ft.Container(
                        content=ft.Image(src=qr_image_path, width=220, height=220),
                        bgcolor="white", padding=10, border_radius=10, alignment=ft.alignment.center
                    ),
                    ft.Row([
                        ft.TextField(value=save_link, read_only=True, expand=True, text_size=10, border_radius=8),
                        ft.IconButton(icon=ft.Icons.COPY, on_click=lambda ev: page.set_clipboard(save_link))
                    ]),
                    ft.ElevatedButton("Open Google Wallet", icon=ft.Icons.OPEN_IN_NEW, on_click=lambda ev: page.launch_url(save_link),
                                      bgcolor="#4285F4", color="white", width=380, height=45)
                ], spacing=12, tight=True, width=400, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                on_dismiss=dialog_dismissed,
                actions=[
                    ft.TextButton("Close", on_click=close_dlg),
                ],
            )
            page.open(qr_dlg)

            status_text.value = "✅ Link generated"
            status_text.color = "green"
        except Exception as ex:
            status_text.value = f"❌ Error: {ex}"
            status_text.color = "red"
        page.update()

    # ── Startup Logic ──
    class_dropdown.on_change = on_class_change
    pass_dropdown.on_change = on_pass_change
    
    load_classes()
    state.register_refresh_callback("g_manage_passes_refresh", load_classes)

    # ── Final Layout ──
    return ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        content=ft.Column([
            ft.Text("Manage Google Passes", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
            ft.Text("Select a template then a pass to view and edit details.", color=TEXT_MUTED, size=13),
            ft.Container(height=10),
            
            class_dropdown,
            ft.Container(height=5),
            pass_dropdown,
            ft.Container(height=10),
            
            edit_form,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
    )
