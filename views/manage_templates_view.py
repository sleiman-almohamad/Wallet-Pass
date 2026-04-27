import flet as ft
from ui.components.json_form_mapper import DynamicForm
from ui.components.text_module_row_editor import TextModuleRowEditor
from core.json_templates import get_editable_fields
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR, BORDER_COLOR
from ui.components.color_picker import create_color_picker
import configs
import httpx


def build_manage_templates_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Manage Templates tab content.
    """
    ts = state.template_state  # shorthand for the sub-state

    # ── Local mutable refs ──
    manage_dynamic_form = None
    manage_current_json = {}
    manage_current_class_type = None
    manage_row_editor = None
    
    # Branding Refs
    issuer_name_tf = ft.TextField(label="Issuer Name (Card Title)", expand=1, border_radius=8, text_size=13)
    header_text_tf = ft.TextField(label="Top Row: Header Value", expand=1, border_radius=8, text_size=13)
    subheader_text_tf = ft.TextField(label="Top Row: Subheader Value", expand=1, border_radius=8, text_size=13)
    logo_url_tf = ft.TextField(label="Logo URL", expand=1, border_radius=8, text_size=13)
    hero_url_tf = ft.TextField(label="Hero Image URL", expand=1, border_radius=8, text_size=13)
    
    color_state = {"bg_color": "#4285f4"}
    
    def on_color_change():
        pass # Optional live sync if we had a preview here
        
    color_picker_container = ft.Container()

    # ── File Picker Logic ──
    current_picker_target = None
    
    def on_file_result(e: ft.FilePickerResultEvent):
        nonlocal current_picker_target
        if e.files and current_picker_target:
            file = e.files[0]
            try:
                # Use public URL if available, otherwise base_url
                api_url = api_client.base_url
                upload_endpoint = f"{api_url}/upload/image"
                
                with open(file.path, "rb") as f:
                    files = {"file": (file.name, f)}
                    response = httpx.post(upload_endpoint, files=files)
                    
                if response.status_code == 200:
                    uploaded_url = response.json().get("url")
                    current_picker_target.value = uploaded_url
                    current_picker_target.update()
                else:
                    _set_status(f"❌ Upload failed: {response.text}", "red")
            except Exception as ex:
                _set_status(f"❌ File picker error: {ex}", "red")
        current_picker_target = None
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def pick_image_for(target_tf):
        nonlocal current_picker_target
        current_picker_target = target_tf
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # Main container
    main_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR
    )

    # ── UI Controls ──
    manage_templates_dropdown = ft.Dropdown(
        label="Select Class ID",
        width=380, border_radius=8, text_size=13,
        options=[],
        on_change=lambda e: show_template(e)
    )

    manage_status = ft.Text("", size=12)

    manage_form_container = ft.Column(
        controls=[ft.Text("Select a Class ID above to load details.", color=TEXT_SECONDARY, size=11)],
        spacing=8,
        scroll="auto",
    )

    branding_container = ft.Column(visible=False, spacing=15)

    def _set_status(msg, color="green"):
        manage_status.value = msg
        manage_status.color = color
        page.update()

    def load_template_classes():
        try:
            classes = api_client.get_classes() if api_client else []
            if classes and len(classes) > 0:
                manage_templates_dropdown.options = [
                    ft.dropdown.Option(key=cls["class_id"], text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})")
                    for cls in classes
                ]
                # Keep current selection if valid, else pick first
                if not manage_templates_dropdown.value or manage_templates_dropdown.value not in [c['class_id'] for c in classes]:
                    manage_templates_dropdown.value = classes[0]["class_id"]
                
                manage_templates_dropdown.hint_text = ""
                _set_status(state.t("msg.loaded_classes", count=len(classes)))
                show_template(None)
            else:
                manage_templates_dropdown.options = []
                manage_templates_dropdown.value = None
                manage_templates_dropdown.hint_text = state.t("msg.no_templates")
                _set_status(state.t("msg.no_templates"), "blue")
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading classes: {e}", "red")

    state.register_refresh_callback("manage_templates_list", load_template_classes)

    def show_template(e):
        nonlocal manage_current_json, manage_current_class_type, manage_dynamic_form, manage_row_editor

        if not manage_templates_dropdown.value:
            return

        _set_status(state.t("msg.loading_template"), "blue")

        try:
            class_id = manage_templates_dropdown.value
            class_data = api_client.get_class(class_id)
            if not class_data:
                _set_status("❌ Template not found", "red"); return

            class_type = class_data.get("class_type", "Generic")
            manage_current_class_type = class_type
            
            # Populate Branding
            issuer_name_tf.value = class_data.get("issuer_name", "")
            logo_url_tf.value = class_data.get("logo_url", "")
            hero_url_tf.value = class_data.get("hero_image_url", "")
            base_color = class_data.get("base_color") or "#4285f4"
            color_state["bg_color"] = base_color
            
            # Subheader / Header (Top Row)
            header_text_tf.value = class_data.get("header", "")
            subheader_text_tf.value = class_data.get("subheader", "")

            # Rebuild color picker to show current color
            color_picker_container.content = create_color_picker(
                page, 
                color_state, 
                on_change_callback=on_color_change,
                color_key="bg_color"
            )
            branding_container.visible = True

            # Use class_json for dynamic form if not Generic
            json_data = class_data.get("class_json", {})
            manage_current_json = json_data.copy()

            field_mappings = get_editable_fields(class_type)
            
            # Exclude fields handled by branding section if Generic
            if class_type == "Generic":
                # For Generic, dynamic form only handles Text Modules Blueprint
                initial_rows = class_data.get("text_module_rows", [])
                manage_row_editor = TextModuleRowEditor(initial_rows, state=state, mode="class")
                manage_dynamic_form = DynamicForm(
                    field_mappings={}, 
                    initial_json={}, 
                    state=state, 
                    custom_controls=[manage_row_editor]
                )
            else:
                manage_row_editor = None
                manage_dynamic_form = DynamicForm(
                    field_mappings, 
                    manage_current_json, 
                    state=state, 
                    on_change_callback=lambda d: None
                )

            manage_form_container.controls = manage_dynamic_form.build()
            _set_status(state.t("msg.template_loaded"))
            
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_and_sync_handler(e):
        nonlocal manage_current_json, manage_dynamic_form, manage_row_editor

        if not manage_templates_dropdown.value:
            return

        _set_status("⏳ Saving and Syncing...", "blue")
        try:
            class_id = manage_templates_dropdown.value
            
            # Collect Branding
            update_data = {
                "issuer_name": issuer_name_tf.value,
                "logo_url": logo_url_tf.value,
                "hero_image_url": hero_url_tf.value,
                "base_color": color_state["bg_color"],
                "header": header_text_tf.value,
                "subheader": subheader_text_tf.value,
                "card_title": issuer_name_tf.value, # Consistency
            }

            if manage_dynamic_form:
                update_data["class_json"] = manage_dynamic_form.get_json_data() if manage_current_class_type != "Generic" else {}
            
            if manage_row_editor:
                update_data["text_module_rows"] = manage_row_editor.get_rows()

            response = api_client.update_class(
                class_id=class_id,
                class_type=manage_current_class_type,
                sync_to_google=True,
                **update_data
            )
            
            save_dlg = ft.AlertDialog(
                title=ft.Text("✅ Template Saved"),
                content=ft.Text("Successfully updated locally and pushed to Google."),
                actions=[ft.TextButton("Perfect", on_click=lambda _: page.close(save_dlg))]
            )
            page.open(save_dlg)
            load_template_classes()
            
        except Exception as ex:
            _set_status(f"❌ Error: {ex}", "red")

    # ── Startup ──
    load_template_classes()

    branding_section = card(ft.Column([
        section_title("Visual Branding & Layout", ft.Icons.PALETTE),
        ft.Row([
            issuer_name_tf,
            ft.Container(width=10),
            ft.Column([
                header_text_tf,
                subheader_text_tf
            ], expand=1)
        ]),
        ft.Row([
            ft.Column([
                ft.Row([logo_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(logo_url_tf))]),
                ft.Row([hero_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(hero_url_tf))]),
            ], expand=1),
            color_picker_container
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=15))

    # Assemble final layout
    branding_container.controls = [
        branding_section,
        card(ft.Column([
            section_title("Face Layout (Text Modules)", ft.Icons.DASHBOARD_CUSTOMIZE),
            manage_form_container,
        ], spacing=12)),
    ]

    main_panel.content = ft.Column([
        ft.Text("Template Editor (Google Wallet)", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
        ft.Text("Design the appearance and layout of your passes.", color=TEXT_SECONDARY, size=13),
        ft.Container(height=8),
        manage_templates_dropdown,
        branding_container,

        ft.Container(
            content=ft.ElevatedButton(
                "Save & Push Changes",
                icon=ft.Icons.CLOUD_UPLOAD,
                on_click=update_and_sync_handler,
                bgcolor=PRIMARY, color="white", height=45, width=220,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            padding=ft.padding.only(top=10),
            alignment=ft.alignment.center_right
        ),
        manage_status
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    return ft.Container(content=main_panel, expand=True, bgcolor=BG_COLOR)
