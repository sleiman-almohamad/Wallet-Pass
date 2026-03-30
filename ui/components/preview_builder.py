import flet as ft
from typing import Dict, Optional

def build_comprehensive_preview(class_data: Dict, pass_data: Optional[Dict] = None, state=None, platform: str = "google") -> ft.Container:
    """
    Build a comprehensive visual pass preview integrating both class and pass object data.
    This centralized function is used across the Template Builder, Pass Generator,
    Manage Templates, and Manage Passes tabs.
    """
    if pass_data is None:
        pass_data = {}

    # Extract properties
    bg_color = pass_data.get("hexBackgroundColor") or class_data.get("hexBackgroundColor") or class_data.get("base_color", "#4285f4")
    
    # 1. Logo Extraction
    logo_url = None
    for src in [pass_data, class_data]:
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
    for src in [pass_data, class_data]:
        if "heroImage" in src:
            hero_url = src.get("heroImage", {}).get("sourceUri", {}).get("uri")
        elif "hero_image_url" in src:
            hero_url = src.get("hero_image_url")
        elif "hero_image" in src:
            hero_url = src.get("hero_image")
        if hero_url:
            break

    # 3. Card Title Extraction
    card_title = "Wallet Pass"
    for src in [pass_data, class_data]:
        if "cardTitle" in src:
            card_title = src.get("cardTitle", {}).get("defaultValue", {}).get("value", card_title)
        elif "card_title" in src:
            # Check if it's a dict or a string (some parts of the app use different structures)
            val = src.get("card_title")
            if isinstance(val, dict):
                card_title = val.get("defaultValue", {}).get("value", card_title)
            else:
                card_title = val or card_title
                
        if card_title != "Wallet Pass":
            break

    # 4. Text Modules
    text_modules = pass_data.get("textModulesData", [])
    
    # Fallback for Template View: If no pass data, use template rows
    if not text_modules and class_data.get("text_module_rows"):
        rows = class_data.get("text_module_rows", [])
        for row in rows:
            # Each row can have Left, Middle, Right modules
            if "left" in row and row["left"]:
                text_modules.append({"header": row["left"], "body": "Sample Value"})
            if "middle" in row and row["middle"]:
                text_modules.append({"header": row["middle"], "body": "Sample Value"})
            if "right" in row and row["right"]:
                text_modules.append({"header": row["right"], "body": "Sample Value"})

    # Prepare modules in rows (max 3 per row)
    module_rows = []
    current_row = []
    for module in text_modules:
        header = module.get("header", "")
        body = module.get("body", "")
        
        col = ft.Column([
            ft.Text(header.upper(), size=10, color="white70", weight="w400"),
            ft.Text(body, size=14, color="white", weight="bold", no_wrap=True, overflow="ellipsis"),
        ], spacing=2, tight=True, expand=True)
        
        current_row.append(col)
        if len(current_row) == 3:
            module_rows.append(ft.Row(current_row, spacing=20, alignment="start"))
            current_row = []
            
    if current_row:
        # Fill the rest with empty containers if needed for alignment, but Row handles it
        module_rows.append(ft.Row(current_row, spacing=20, alignment="start"))

    # 5. Holder Info
    holder_name = pass_data.get("holder_name") or "Holder Name"

    # Build UI Components
    
    # Header Row
    header_section = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=20, bottom=10),
        content=ft.Row([
            ft.Container(
                width=40, height=40, border_radius=20,
                bgcolor="white24" if not logo_url else None,
                clip_behavior="antiAlias",
                content=ft.Image(
                    src=logo_url,
                    fit="cover",
                ) if logo_url else ft.Icon("image", color="white30", size=20),
            ),
            ft.Text(card_title, size=18, weight="bold", color="white", expand=True),
        ], vertical_alignment="center", spacing=15),
    )

    # Hero Image Section
    hero_section = ft.Container()
    if hero_url:
        hero_section = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Container(
                width=280, height=120, border_radius=12,
                clip_behavior="antiAlias",
                content=ft.Image(
                    src=hero_url,
                    fit="cover",
                ),
                shadow=ft.BoxShadow(blur_radius=10, color="black26"),
            )
        )
    else:
        # Minimal height if no hero image
        hero_section = ft.Container(height=10)

    # Text Modules Section
    modules_section = ft.Container(
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        content=ft.Column(module_rows, spacing=15),
        expand=True,
    )

    # Barcode Section
    barcode_section = ft.Container(
        margin=ft.margin.only(top=10),
        padding=ft.padding.only(bottom=20, left=20, right=20, top=10),
        bgcolor="white",
        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
        content=ft.Column([
            ft.Container(
                alignment=ft.alignment.center,
                padding=10,
                content=ft.Column([
                    ft.Icon("qr_code_2", size=70, color="black87"),
                    ft.Text(holder_name, size=14, color="black54", weight="w500"),
                ], horizontal_alignment="center", spacing=5),
            )
        ], horizontal_alignment="center"),
    )

    # Main Card Container
    return ft.Container(
        width=320,
        height=520,
        bgcolor=bg_color,
        border_radius=20,
        clip_behavior="antiAlias",
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=25,
            color="black26",
            offset=ft.Offset(0, 10),
        ),
        content=ft.Column([
            header_section,
            hero_section,
            modules_section,
            barcode_section,
        ], spacing=0, scroll="hidden"),
    )
