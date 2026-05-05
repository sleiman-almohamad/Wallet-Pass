import flet as ft
from ui.theme import card, section_title, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, BG_COLOR, BORDER_COLOR
import configs
import qrcode
import base64
from io import BytesIO

def build_campaign_management_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the QR Campaign Management view.
    """
    
    # ── Local state ──
    current_view = "list" # "list" or "edit"
    editing_campaign = None
    
    # Editor Refs
    campaign_name_tf = ft.TextField(label=state.t("label.campaign_name"), expand=1, border_radius=8, hint_text="")
    slug_tf = ft.TextField(label=state.t("label.url_slug"), expand=1, border_radius=8, hint_text="")
    
    landing_title_tf = ft.TextField(label=state.t("label.landing_title"), expand=1, border_radius=8)
    landing_subtitle_tf = ft.TextField(label=state.t("label.landing_subtitle"), expand=1, border_radius=8, multiline=True)
    
    google_class_dd = ft.Dropdown(label=state.t("label.google_class"), expand=1, border_radius=8)
    apple_template_dd = ft.Dropdown(label=state.t("label.apple_template"), expand=1, border_radius=8)
    
    # ── UI Containers ──
    campaigns_list_column = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("", size=12)
    view_content = ft.Column(expand=True)

    def load_campaigns():
        campaigns_list_column.controls.clear()
        try:
            campaigns = api_client.get_campaigns()
            if not campaigns:
                campaigns_list_column.controls.append(
                    ft.Text(state.t("msg.no_campaigns"), 
                            color=TEXT_SECONDARY, size=13, italic=True)
                )
            else:
                for c in campaigns:
                    campaigns_list_column.controls.append(create_campaign_card(c))
        except Exception as e:
            status_text.value = f"❌ {state.t('msg.api_error', detail=str(e))}"
            status_text.color = "red"
        render_view()

    def show_editor(campaign=None):
        nonlocal current_view, editing_campaign
        current_view = "edit"
        editing_campaign = campaign
        
        # Load dropdowns
        try:
            google_classes = api_client.get_classes()
            apple_templates = api_client.get_apple_templates()
            
            google_class_dd.options = [ft.dropdown.Option(c['class_id'], c['class_id']) for c in google_classes]
            apple_template_dd.options = [ft.dropdown.Option(t['template_id'], t['template_name']) for t in apple_templates]
        except:
            pass

        if campaign:
            campaign_name_tf.value = campaign.get("campaign_name", "")
            slug_tf.value = campaign.get("slug", "")
            landing_title_tf.value = campaign.get("landing_title", "")
            landing_subtitle_tf.value = campaign.get("landing_subtitle", "")
            google_class_dd.value = campaign.get("google_class_id")
            apple_template_dd.value = campaign.get("apple_template_id")
            slug_tf.read_only = True
        else:
            campaign_name_tf.value = ""
            slug_tf.value = ""
            landing_title_tf.value = state.t("default.landing_title")
            landing_subtitle_tf.value = state.t("default.landing_subtitle")
            google_class_dd.value = None
            apple_template_dd.value = None
            slug_tf.read_only = False
            
        render_view()

    def save_campaign(e):
        try:
            data = {
                "campaign_name": campaign_name_tf.value,
                "slug": slug_tf.value,
                "google_class_id": google_class_dd.value,
                "apple_template_id": apple_template_dd.value,
                "landing_title": landing_title_tf.value,
                "landing_subtitle": landing_subtitle_tf.value,
            }
            
            if editing_campaign:
                api_client.update_campaign(editing_campaign["id"], **data)
            else:
                api_client.create_campaign(**data)
            
            nonlocal current_view
            current_view = "list"
            load_campaigns()
        except Exception as ex:
            status_text.value = f"❌ {state.t('msg.api_error', detail=str(ex))}"
            status_text.color = "red"
            page.update()

    def delete_campaign(cid):
        try:
            api_client.delete_campaign(cid)
            load_campaigns()
        except Exception as e:
            status_text.value = f"❌ {state.t('msg.api_error', detail=str(e))}"
            status_text.color = "red"
            page.update()

    def generate_styled_qr(data, label):
        """Generate a QR code with the campaign name styled below it."""
        from PIL import Image, ImageDraw, ImageFont
        try:
            # 1. Create QR
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            
            # 2. Add Label
            width, height = qr_img.size
            padding = 40
            new_height = height + padding
            
            # Create a new white canvas
            canvas = Image.new("RGB", (width, new_height), "white")
            canvas.paste(qr_img, (0, 0))
            
            # Draw text
            draw = ImageDraw.Draw(canvas)
            # Try to get a decent font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
                
            # Center text
            text_box = draw.textbbox((0, 0), label, font=font)
            text_width = text_box[2] - text_box[0]
            text_x = (width - text_width) // 2
            text_y = height - 5
            
            draw.text((text_x, text_y), label, fill=PRIMARY, font=font)
            
            # 3. Export to Base64
            buffered = BytesIO()
            canvas.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return img_str
        except Exception as e:
            print(f"QR Gen Error: {e}")
            return None

    def create_campaign_card(c):
        # Generate URL
        public_url = getattr(configs, "PUBLIC_URL", "http://localhost:8100")
        campaign_url = f"{public_url}/c/{c['slug']}"
        
        # Generate QR
        qr_b64 = generate_styled_qr(campaign_url, c['campaign_name'])
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Image(
                            src_base64=qr_b64,
                            width=80,
                            height=90,
                            fit=ft.ImageFit.CONTAIN,
                            tooltip=state.t("tooltip.download_qr")
                        ) if qr_b64 else ft.Icon(ft.Icons.QR_CODE_2, color=PRIMARY, size=32),
                        on_click=lambda _: page.launch_url(f"{getattr(configs, 'PUBLIC_URL', 'http://localhost:8100')}/api/campaigns/{c['id']}/qr"),
                        tooltip=state.t("tooltip.download_qr")
                    ),
                    ft.Column([
                        ft.Text(c['campaign_name'], size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(f"Slug: /{c['slug']}", size=12, color=PRIMARY, weight=ft.FontWeight.W_600),
                    ], spacing=2, expand=True),
                    ft.Row([
                        ft.IconButton(ft.Icons.COPY_ALL, tooltip=state.t("tooltip.copy_link"), on_click=lambda _: page.set_clipboard(campaign_url)),
                        ft.IconButton(ft.Icons.OPEN_IN_NEW, tooltip=state.t("tooltip.open_landing"), on_click=lambda _: page.launch_url(campaign_url)),
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, on_click=lambda _: show_editor(c), tooltip=state.t("tooltip.edit_campaign")),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red700", on_click=lambda _: delete_campaign(c['id']))
                    ])
                ]),
                ft.Divider(height=1, color=BORDER_COLOR),
                ft.Row([
                    ft.Icon(ft.Icons.ANDROID, size=16, color=TEXT_SECONDARY),
                    ft.Text(f"Google: {c['google_class_id'] or 'None'}", size=11, color=TEXT_SECONDARY),
                    ft.Container(width=10),
                    ft.Icon(ft.Icons.APPLE, size=16, color=TEXT_SECONDARY),
                    ft.Text(f"Apple: {c['apple_template_id'] or 'None'}", size=11, color=TEXT_SECONDARY),
                ])
            ], spacing=10),
            padding=15, border=ft.border.all(1, BORDER_COLOR), border_radius=12, bgcolor="white"
        )

    def render_view():
        view_content.controls.clear()
        if current_view == "list":
            view_content.controls = [
                ft.Row([
                    ft.Column([
                        ft.Text(state.t("header.qr_campaigns"), size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                        ft.Text(state.t("subtitle.qr_campaigns"), color=TEXT_SECONDARY, size=13),
                    ], expand=True),
                    ft.ElevatedButton(state.t("btn.create_campaign"), icon=ft.Icons.ADD, on_click=lambda _: show_editor(), bgcolor=PRIMARY, color="white")
                ]),
                ft.Container(height=10),
                status_text,
                ft.Container(content=campaigns_list_column, expand=True)
            ]
        else:
            # Editor View
            view_content.controls = [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: back_to_list()),
                    ft.Text(state.t("header.campaign_designer"), size=26, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                ]),
                ft.Container(height=10),
                ft.Column([
                    card(ft.Column([
                        section_title(state.t("header.campaign_identity"), ft.Icons.LABEL),
                        ft.Row([campaign_name_tf, slug_tf]),
                    ], spacing=15)),
                    
                    card(ft.Column([
                        section_title(state.t("header.wallet_routing"), ft.Icons.ROUTE),
                        ft.Text(state.t("msg.assign_templates_hint"), size=12, color=TEXT_SECONDARY),
                        ft.Row([google_class_dd, apple_template_dd]),
                    ], spacing=15)),

                    card(ft.Column([
                        section_title(state.t("header.landing_page_design"), ft.Icons.WEB),
                        landing_title_tf,
                        landing_subtitle_tf,
                    ], spacing=15)),

                    # QR Code Preview & Download
                    card(ft.Column([
                        section_title(state.t("header.distribution_qr"), ft.Icons.QR_CODE_2),
                        ft.Text(state.t("msg.download_qr_hint"), size=12, color=TEXT_SECONDARY),
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Image(
                                        src_base64=generate_styled_qr(
                                            (getattr(configs, 'PUBLIC_URL', 'http://localhost:8100') + '/c/' + slug_tf.value) if slug_tf.value else "https://yourlink.com", 
                                            campaign_name_tf.value or "Campaign"
                                        ),
                                        width=150, height=180, fit=ft.ImageFit.CONTAIN,
                                        tooltip=state.t("tooltip.download_qr")
                                    ),
                                    ft.ElevatedButton(
                                        state.t("btn.download_qr"), icon=ft.Icons.DOWNLOAD,
                                        on_click=lambda _: page.launch_url(f"{getattr(configs, 'PUBLIC_URL', 'http://localhost:8100')}/api/campaigns/{editing_campaign['id']}/qr")
                                    )
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=10, border=ft.border.all(1, BORDER_COLOR), border_radius=8,
                                alignment=ft.alignment.center
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=15)) if editing_campaign else ft.Container(),

                    ft.Container(
                        content=ft.ElevatedButton(
                            state.t("btn.save_campaign"), icon=ft.Icons.SAVE, on_click=save_campaign,
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
        load_campaigns()

    # Initial load
    load_campaigns()

    return ft.Container(
        expand=True, padding=ft.padding.only(left=36, right=36, top=24, bottom=20),
        bgcolor=BG_COLOR, content=view_content
    )
