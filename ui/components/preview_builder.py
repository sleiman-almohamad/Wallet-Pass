import flet as ft
from typing import Dict, Optional

def build_comprehensive_preview(class_data: Dict, pass_data: Optional[Dict] = None, state=None) -> ft.Container:
    """
    Build a comprehensive visual pass preview integrating both class and pass object data.
    This centralized function is used across the Template Builder, Pass Generator,
    Manage Templates, and Manage Passes tabs.
    """
    if pass_data is None:
        pass_data = {}

    bg_color = pass_data.get("hexBackgroundColor") or class_data.get("hexBackgroundColor") or class_data.get("base_color", "#4285f4")
    class_type = class_data.get("class_type", "Generic")

    # 1. Logo Extraction
    logo_url = None
    for src in [class_data, pass_data]:
        if "programLogo" in src:
            logo_url = src.get("programLogo", {}).get("sourceUri", {}).get("uri")
        elif "logo" in src:
            logo_url = src.get("logo", {}).get("sourceUri", {}).get("uri")
        elif "logo_url" in src:
            logo_url = src.get("logo_url")
        if logo_url:
            break

    # 2. Hero Image Extraction
    hero_url = None
    for src in [class_data, pass_data]:
        if "heroImage" in src:
            hero_url = src.get("heroImage", {}).get("sourceUri", {}).get("uri")
        elif "hero_image_url" in src:
            hero_url = src.get("hero_image_url")
        elif "hero_image" in src:
            hero_url = src.get("hero_image")
        if hero_url:
            break

    # 3. Header / Title Extraction
    header_text = state.t("placeholder.business_name") if state else "Business Name"
    card_title = state.t("placeholder.pass_title") if state else "Pass Title"

    for src in [class_data, pass_data]:
        if "localizedIssuerName" in src:
            header_text = src.get("localizedIssuerName", {}).get("defaultValue", {}).get("value", header_text)
        elif "issuerName" in src:
            header_text = src.get("issuerName", header_text)
        elif "issuer_name" in src:
            header_text = src.get("issuer_name", header_text)

        if "localizedProgramName" in src:
            card_title = src.get("localizedProgramName", {}).get("defaultValue", {}).get("value", card_title)
        elif "eventName" in src:
            card_title = src.get("eventName", {}).get("defaultValue", {}).get("value", card_title)
        elif "header" in src:
            header_text = src.get("header", {}).get("defaultValue", {}).get("value", header_text)
        if "cardTitle" in src:
            card_title = src.get("cardTitle", {}).get("defaultValue", {}).get("value", card_title)
        elif "card_title" in src:
            card_title = src.get("card_title", card_title)

    # 4. Holder Info
    holder_name = pass_data.get("holder_name", state.t("label.sample_user") if state else "Pass Holder")

    # Build Logo Control
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

    # Build Hero Control
    if hero_url:
        hero_control = ft.Container(
            height=150,
            content=ft.Image(src=hero_url, width=300, height=150, fit=ft.ImageFit.COVER),
        )
    else:
        hero_control = ft.Container(
            height=150, bgcolor="black12",
            content=ft.Column(
                [ft.Icon("image", size=40, color="grey"), ft.Text(state.t("placeholder.hero_image") if state else "Hero Image", size=12, color="grey")],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # 5. Extract Detailed Fields by Class Type
    detail_lines = []

    if class_type == "EventTicket":
        if 'seat_number' in pass_data and pass_data.get('seat_number'):
            detail_lines.append((state.t("label.seat") if state else "Seat", pass_data.get('seat_number')))
        if 'event_time' in pass_data and pass_data.get('event_time'):
            detail_lines.append((state.t("label.time") if state else "Time", pass_data.get('event_time')))
        if 'gate' in pass_data and pass_data.get('gate'):
            detail_lines.append((state.t("label.gate") if state else "Gate", pass_data.get('gate')))

    elif class_type == "LoyaltyCard":
        detail_lines.append((state.t("label.points") if state else "Points", pass_data.get('points_balance', '0')))
        detail_lines.append((state.t("label.tier") if state else "Tier", pass_data.get('tier_level', 'Standard')))
        if 'account_name' in pass_data:
            detail_lines.append((state.t("label.account") if state else "Account", pass_data.get('account_name')))

    elif class_type == "GiftCard":
        balance = pass_data.get('balance') or class_data.get('balance', '0.00')
        detail_lines.append((state.t("label.balance") if state else "Balance", f"${balance}"))
        if 'card_number' in pass_data:
            detail_lines.append((state.t("label.card_number") if state else "Card", pass_data.get('card_number')))
        if 'pin' in pass_data:
            detail_lines.append((state.t("label.pin") if state else "PIN", pass_data.get('pin')))

    elif class_type == "TransitPass":
        detail_lines.append((state.t("label.type") if state else "Type", pass_data.get('pass_type', 'Standard')))
        if pass_data.get('valid_from') and pass_data.get('valid_until'):
            detail_lines.append((state.t("label.valid") if state else "Valid", f"{pass_data.get('valid_from')} - {pass_data.get('valid_until')}"))

    # 6. Extract Text Module Rows
    # Combine rows from class and pass priorities (pass overrides or appends)
    text_modules = []
    
    class_modules = class_data.get("textModulesData", [])
    if isinstance(class_modules, list):
        text_modules.extend(class_modules)
        
    pass_modules = pass_data.get("textModulesData", [])
    if isinstance(pass_modules, list):
        text_modules.extend(pass_modules)

    for module in text_modules:
        if isinstance(module, dict):
            h = module.get("header")
            b = module.get("body")
            if h or b:
                detail_lines.append((h or (state.t("label.info") if state else "Info"), b or ""))

    # Extra Details Control
    details_controls = [
        ft.Text(state.t("label.pass_details") if state else "Pass Details", color="grey", size=11, weight=ft.FontWeight.W_500),
        ft.Divider(height=10, color="grey300")
    ]
    
    if detail_lines:
        for header, body in detail_lines:
            details_controls.append(
                ft.Row([
                    ft.Text(f"{header}:", weight=ft.FontWeight.BOLD, size=12, color="black87", width=100),
                    ft.Text(str(body), size=12, color="black54", expand=True)
                ])
            )
            details_controls.append(ft.Container(height=2))
    else:
        details_controls.append(ft.Text(state.t("msg.no_details") if state else "No additional details", size=12, color="grey500", italic=True))

    return ft.Container(
        width=300,
        bgcolor=bg_color,
        border_radius=15,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        shadow=ft.BoxShadow(blur_radius=15, color="black26", offset=ft.Offset(0, 5)),
        content=ft.Column([
            # Top Header
            ft.Container(
                padding=15,
                content=ft.Row([
                    logo_control,
                    ft.Container(width=10),
                    ft.Text(header_text, color="white", weight=ft.FontWeight.BOLD, size=14, expand=True),
                ]),
            ),
            # Title
            ft.Container(
                padding=ft.padding.only(left=15, right=15, bottom=10),
                content=ft.Text(card_title, color="white", size=20, weight=ft.FontWeight.BOLD),
            ),
            # Hero Graphic
            hero_control,
            # Barcode / QR
            ft.Container(
                bgcolor="white", padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            width=70, height=70, bgcolor="grey200", border_radius=5,
                            content=ft.Icon("qr_code_2", size=50, color="grey"),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(holder_name, weight=ft.FontWeight.BOLD, size=13, color="black"),
                            ft.Text(f"ID: {pass_data.get('object_id') or '...preview...'}", size=11, color="grey"),
                        ]),
                    ]),
                    ft.Container(height=15),
                    # Dynamic Details Column
                    *details_controls
                ]),
            ),
        ], spacing=0),
    )
