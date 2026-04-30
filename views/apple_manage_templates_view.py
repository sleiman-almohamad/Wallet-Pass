import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR, BORDER_COLOR
from ui.components.color_picker import create_color_picker
from ui.components.apple_field_editor import AppleFieldEditor
import configs
import httpx


def build_apple_manage_templates_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Apple Manage Templates view using a dropdown layout exactly like the Google template editor.
    """
    # ── Local state ──
    editing_template = None
    
    # Editor Refs
    template_name_tf = ft.TextField(label="Template Name", expand=1, border_radius=8, text_size=13)
    pass_style_dd = ft.Dropdown(
        label="Pass Style",
        options=[
            ft.dropdown.Option("generic", "Generic"),
            ft.dropdown.Option("storecard", "Store Card"),
            ft.dropdown.Option("coupon", "Coupon"),
            ft.dropdown.Option("eventticket", "Event Ticket"),
            ft.dropdown.Option("boardingpass", "Boarding Pass"),
        ],
        expand=1, border_radius=8, text_size=13
    )
    org_name_tf = ft.TextField(label="Organization Name", expand=1, border_radius=8, text_size=13)
    logo_text_tf = ft.TextField(label="Logo Text", expand=1, border_radius=8, text_size=13)
    pass_type_id_tf = ft.TextField(label="Pass Type ID", expand=1, border_radius=8, text_size=13, value=configs.APPLE_PASS_TYPE_ID)
    team_id_tf = ft.TextField(label="Team ID", expand=1, border_radius=8, text_size=13, value=configs.APPLE_TEAM_ID)
    
    logo_icon_url_tf = ft.TextField(label="Logo & Icon URL", expand=1, border_radius=8, text_size=13)
    strip_url_tf = ft.TextField(label="Strip (Hero) URL", expand=1, border_radius=8, text_size=13)
    
    colors = {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "label": "#666666"
    }
    
    color_picker_container_bg = ft.Container()
    color_picker_container_fg = ft.Container()
    color_picker_container_lbl = ft.Container()
    
    field_editor = AppleFieldEditor(page=page)
    
    # ── File Picker Logic ──
    current_picker_target = None
    def on_file_result(e: ft.FilePickerResultEvent):
        nonlocal current_picker_target
        if e.files and current_picker_target:
            file = e.files[0]
            try:
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

    # ── UI Controls ──
    apple_templates_dropdown = ft.Dropdown(
        label="Select Template ID",
        width=380, border_radius=8, text_size=13,
        options=[],
        on_change=lambda e: show_template(e)
    )

    manage_status = ft.Text("", size=12)

    branding_container = ft.Column(visible=False, spacing=15)

    def _set_status(msg, color="green"):
        manage_status.value = msg
        manage_status.color = color
        page.update()

    def load_templates():
        try:
            templates = api_client.get_apple_templates() if api_client else []
            if templates and len(templates) > 0:
                apple_templates_dropdown.options = [
                    ft.dropdown.Option(key=t["template_id"], text=f"{t['template_name']} ({t.get('pass_style', 'Unknown')})")
                    for t in templates
                ]
                if not apple_templates_dropdown.value or apple_templates_dropdown.value not in [t['template_id'] for t in templates]:
                    apple_templates_dropdown.value = templates[0]["template_id"]
                
                apple_templates_dropdown.hint_text = ""
                _set_status(f"Loaded {len(templates)} templates")
                show_template(None)
            else:
                apple_templates_dropdown.options = []
                apple_templates_dropdown.value = None
                apple_templates_dropdown.hint_text = "No Apple templates found"
                _set_status("No Apple templates found", "blue")
                branding_container.visible = False
            page.update()
        except Exception as e:
            _set_status(f"❌ Error loading templates: {e}", "red")

    state.register_refresh_callback("apple_manage_templates_list", load_templates)

    def show_template(e):
        nonlocal editing_template

        if not apple_templates_dropdown.value:
            return

        _set_status("Loading template blueprint...", "blue")

        try:
            tid = apple_templates_dropdown.value
            templates = api_client.get_apple_templates()
            template = next((t for t in templates if t["template_id"] == tid), None)
            
            if not template:
                _set_status("❌ Template blueprint not found", "red"); return

            editing_template = template
            
            template_name_tf.value = template.get("template_name", "")
            pass_style_dd.value = template.get("pass_style", "generic")
            org_name_tf.value = template.get("organization_name", "")
            logo_text_tf.value = template.get("logo_text", "")
            pass_type_id_tf.value = template.get("pass_type_identifier", configs.APPLE_PASS_TYPE_ID)
            team_id_tf.value = template.get("team_identifier", configs.APPLE_TEAM_ID)
            
            logo_icon_url_tf.value = template.get("logo_url") or template.get("icon_url") or ""
            strip_url_tf.value = template.get("strip_url", "")
            
            colors["bg"] = template.get("background_color") or "#FFFFFF"
            colors["fg"] = template.get("foreground_color") or "#000000"
            colors["label"] = template.get("label_color") or "#666666"
            
            field_editor.load_fields(template.get("fields", []))

            # Rebuild color pickers
            color_picker_container_bg.content = create_color_picker(page, colors, lambda: None, "bg", "Background")
            color_picker_container_fg.content = create_color_picker(page, colors, lambda: None, "fg", "Foreground (Text)")
            color_picker_container_lbl.content = create_color_picker(page, colors, lambda: None, "label", "Label Color")
            
            branding_container.visible = True
            _set_status("Template loaded")
            
        except Exception as ex:
            _set_status(f"❌ Error: {ex}", "red")
        page.update()

    def update_and_sync_handler(e):
        if not apple_templates_dropdown.value:
            return

        _set_status("⏳ Saving Blueprint Changes...", "blue")
        try:
            tid = apple_templates_dropdown.value
            
            data = {
                "template_name": template_name_tf.value,
                "pass_style": pass_style_dd.value,
                "organization_name": org_name_tf.value,
                "logo_text": logo_text_tf.value,
                "pass_type_identifier": pass_type_id_tf.value,
                "team_identifier": team_id_tf.value,
                "background_color": colors["bg"],
                "foreground_color": colors["fg"],
                "label_color": colors["label"],
                "logo_url": logo_icon_url_tf.value,
                "icon_url": logo_icon_url_tf.value,
                "strip_url": strip_url_tf.value,
                "dynamic_fields": field_editor.get_fields()
            }

            api_client.update_apple_template(tid, **data)
            
            save_dlg = ft.AlertDialog(
                title=ft.Text("✅ Template Blueprint Saved"),
                content=ft.Text("Successfully updated the Apple template locally."),
                actions=[ft.TextButton("Perfect", on_click=lambda _: page.close(save_dlg))]
            )
            page.open(save_dlg)
            load_templates()
            
        except Exception as ex:
            _set_status(f"❌ Error: {ex}", "red")

    def delete_template_handler(e):
        if not apple_templates_dropdown.value:
            return
            
        def confirm_delete(_):
            try:
                tid = apple_templates_dropdown.value
                api_client.delete_apple_template(tid)
                page.close(confirm_dlg)
                apple_templates_dropdown.value = None
                load_templates()
            except Exception as ex:
                _set_status(f"❌ Delete error: {ex}", "red")
        
        confirm_dlg = ft.AlertDialog(
            title=ft.Text("⚠️ Confirm Deletion"),
            content=ft.Text(f"Are you sure you want to delete template '{apple_templates_dropdown.value}'? This cannot be undone."),
            actions=[
                ft.TextButton("Yes, Delete", icon=ft.Icons.DELETE, icon_color="red", on_click=confirm_delete),
                ft.TextButton("Cancel", on_click=lambda _: page.close(confirm_dlg))
            ]
        )
        page.open(confirm_dlg)

    # Initial load
    load_templates()

    # Layout assembling
    branding_section = card(ft.Column([
        section_title("Base & Visual Configuration", ft.Icons.PALETTE),
        ft.Row([template_name_tf, pass_style_dd]),
        ft.Row([org_name_tf, logo_text_tf, pass_type_id_tf, team_id_tf]),
        ft.Row([
            ft.Column([
                ft.Row([logo_icon_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(logo_icon_url_tf))]),
                ft.Row([strip_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(strip_url_tf))]),
            ], expand=1),
            ft.Column([
                color_picker_container_bg,
                color_picker_container_fg,
                color_picker_container_lbl
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=15))

    branding_container.controls = [
        branding_section,
        card(ft.Column([
            section_title("Card Fields (Template Defaults)", ft.Icons.DASHBOARD_CUSTOMIZE),
            field_editor.build()
        ], spacing=10)),
    ]

    main_panel = ft.Container(
        expand=True,
        padding=ft.padding.only(left=36, right=20, top=20, bottom=20),
        bgcolor=BG_COLOR
    )

    main_panel.content = ft.Column([
        ft.Text("Template Editor (Apple Wallet)", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
        ft.Text("Design the appearance and layout of your passes.", color=TEXT_SECONDARY, size=13),
        ft.Container(height=8),
        ft.Row([
            apple_templates_dropdown,
            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red700", tooltip="Delete Template", on_click=delete_template_handler)
        ], alignment=ft.MainAxisAlignment.START),
        branding_container,

        ft.Container(
            content=ft.ElevatedButton(
                "Save Blueprint",
                icon=ft.Icons.SAVE,
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
