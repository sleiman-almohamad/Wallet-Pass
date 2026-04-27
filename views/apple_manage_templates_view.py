import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR, BORDER_COLOR
from ui.components.color_picker import create_color_picker
import configs
import httpx


def build_apple_manage_templates_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Apple Manage Templates view.
    """
    
    # ── Local state ──
    current_view = "list" # "list" or "edit"
    editing_template = None
    
    # Editor Refs
    template_name_tf = ft.TextField(label="Template Name", expand=1, border_radius=8)
    pass_style_dd = ft.Dropdown(
        label="Pass Style",
        options=[
            ft.dropdown.Option("generic", "Generic"),
            ft.dropdown.Option("storecard", "Store Card"),
            ft.dropdown.Option("coupon", "Coupon"),
            ft.dropdown.Option("eventticket", "Event Ticket"),
            ft.dropdown.Option("boardingpass", "Boarding Pass"),
        ],
        expand=1, border_radius=8
    )
    org_name_tf = ft.TextField(label="Organization Name", expand=1, border_radius=8)
    pass_type_id_tf = ft.TextField(label="Pass Type ID", expand=1, border_radius=8, value=configs.APPLE_PASS_TYPE_ID)
    team_id_tf = ft.TextField(label="Team ID", expand=1, border_radius=8, value=configs.APPLE_TEAM_ID)
    
    logo_url_tf = ft.TextField(label="Logo URL", expand=1, border_radius=8)
    icon_url_tf = ft.TextField(label="Icon URL", expand=1, border_radius=8)
    strip_url_tf = ft.TextField(label="Strip (Hero) URL", expand=1, border_radius=8)
    
    colors = {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "label": "#666666"
    }
    
    color_pickers_col = ft.Column(spacing=20)
    
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
                    status_text.value = f"❌ Upload failed: {response.text}"
                    status_text.color = "red"
            except Exception as ex:
                status_text.value = f"❌ File picker error: {ex}"
                status_text.color = "red"
        current_picker_target = None
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def pick_image_for(target_tf):
        nonlocal current_picker_target
        current_picker_target = target_tf
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # ── UI Containers ──
    templates_list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("", size=12)
    view_content = ft.Column(expand=True)

    def load_templates():
        templates_list_column.controls.clear()
        try:
            templates = api_client.get_apple_templates() if api_client else []
            if not templates:
                templates_list_column.controls.append(
                    ft.Text("No Apple templates found.", color=TEXT_SECONDARY, size=13, italic=True)
                )
            else:
                for t in templates:
                    templates_list_column.controls.append(create_template_card(t))
        except Exception as e:
            status_text.value = f"❌ Error: {str(e)}"
            status_text.color = "red"
        render_view()

    def show_editor(template=None):
        nonlocal current_view, editing_template
        current_view = "edit"
        editing_template = template
        
        if template:
            template_name_tf.value = template.get("template_name", "")
            pass_style_dd.value = template.get("pass_style", "generic")
            org_name_tf.value = template.get("organization_name", "")
            pass_type_id_tf.value = template.get("pass_type_identifier", configs.APPLE_PASS_TYPE_ID)
            team_id_tf.value = template.get("team_identifier", configs.APPLE_TEAM_ID)
            logo_url_tf.value = template.get("logo_url", "")
            icon_url_tf.value = template.get("icon_url", "")
            strip_url_tf.value = template.get("strip_url", "")
            colors["bg"] = template.get("background_color") or "#FFFFFF"
            colors["fg"] = template.get("foreground_color") or "#000000"
            colors["label"] = template.get("label_color") or "#666666"
        else:
            template_name_tf.value = "New Template"
            pass_style_dd.value = "generic"
            org_name_tf.value = ""
            logo_url_tf.value = ""
            icon_url_tf.value = ""
            strip_url_tf.value = ""
            colors["bg"] = "#FFFFFF"
            colors["fg"] = "#000000"
            colors["label"] = "#666666"

        # Initialize color pickers
        color_pickers_col.controls = [
            create_color_picker(page, colors, lambda: None, "bg", "Background"),
            create_color_picker(page, colors, lambda: None, "fg", "Foreground (Text)"),
            create_color_picker(page, colors, lambda: None, "label", "Label Color"),
        ]
        
        render_view()

    def save_template(e):
        try:
            data = {
                "template_name": template_name_tf.value,
                "pass_style": pass_style_dd.value,
                "organization_name": org_name_tf.value,
                "pass_type_identifier": pass_type_id_tf.value,
                "team_identifier": team_id_tf.value,
                "background_color": colors["bg"],
                "foreground_color": colors["fg"],
                "label_color": colors["label"],
                "logo_url": logo_url_tf.value,
                "icon_url": icon_url_tf.value,
                "strip_url": strip_url_tf.value,
            }
            
            if editing_template:
                api_client.update_apple_template(editing_template["template_id"], **data)
            else:
                # generate ID
                import uuid
                tid = f"tpl_{str(uuid.uuid4())[:8]}"
                api_client.create_apple_template(template_id=tid, **data)
            
            nonlocal current_view
            current_view = "list"
            load_templates()
        except Exception as ex:
            status_text.value = f"❌ Save error: {ex}"
            status_text.color = "red"
            page.update()

    def delete_template(template_id):
        try:
            api_client.delete_apple_template(template_id)
            load_templates()
        except Exception as e:
            status_text.value = f"❌ Delete error: {str(e)}"
            status_text.color = "red"
            page.update()

    def create_template_card(t):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STYLE, color=PRIMARY, size=24),
                ft.Column([
                    ft.Text(t['template_name'], size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"ID: {t['template_id']} | Style: {t['pass_style']}", size=11, color=TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.IconButton(ft.Icons.EDIT_OUTLINE, on_click=lambda _: show_editor(t), tooltip="Edit Blueprint"),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red700", on_click=lambda _: delete_template(t['template_id']))
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15, border=ft.border.all(1, BORDER_COLOR), border_radius=8, bgcolor="white"
        )

    def render_view():
        view_content.controls.clear()
        if current_view == "list":
            view_content.controls = [
                ft.Row([
                    ft.Column([
                        ft.Text("Apple Templates", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                        ft.Text("List of all Apple Wallet pass templates.", color=TEXT_SECONDARY, size=13),
                    ], expand=True),
                    ft.ElevatedButton("Create New", icon=ft.Icons.ADD, on_click=lambda _: show_editor(), bgcolor=PRIMARY, color="white")
                ]),
                ft.Container(height=10),
                status_text,
                ft.Container(content=templates_list_column, expand=True)
            ]
        else:
            # Editor View
            view_content.controls = [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: back_to_list()),
                    ft.Text("Template Editor (Apple)", size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                ]),
                ft.Container(height=10),
                ft.Column([
                    card(ft.Column([
                        section_title("Base Configuration", ft.Icons.SETTINGS),
                        ft.Row([template_name_tf, pass_style_dd]),
                        ft.Row([org_name_tf, pass_type_id_tf, team_id_tf]),
                    ], spacing=15)),
                    
                    card(ft.Column([
                        section_title("Visual Branding", ft.Icons.PALETTE),
                        ft.Row([
                            ft.Column([
                                ft.Row([logo_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(logo_url_tf))]),
                                ft.Row([icon_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(icon_url_tf))]),
                                ft.Row([strip_url_tf, ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=lambda _: pick_image_for(strip_url_tf))]),
                            ], expand=1),
                            color_pickers_col
                        ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=20)
                    ])),

                    ft.Container(
                        content=ft.ElevatedButton(
                            "Save Blueprint", icon=ft.Icons.SAVE, on_click=save_template,
                            bgcolor=PRIMARY, color="white", height=45, width=200
                        ),
                        alignment=ft.alignment.center_right
                    )
                ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
            ]
        page.update()

    def back_to_list():
        nonlocal current_view
        current_view = "list"
        load_templates()

    # Initial load
    load_templates()

    return ft.Container(
        expand=True, padding=ft.padding.only(left=36, right=36, top=24, bottom=20),
        bgcolor=BG_COLOR, content=view_content
    )
