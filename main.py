import flet as ft
import json
from wallet_service import WalletClient

def main(page: ft.Page):
    page.title = "Google Wallet Verifier & Preview"
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- Initialize Connection ---
    client = None
    try:
        client = WalletClient()
        # FIX: Changed ft.colors.GREEN to "green"
        connection_status = ft.Text("✅ Service Connected", color="green", size=12)
    except Exception as e:
        client = None
        # FIX: Changed ft.colors.RED to "red"
        connection_status = ft.Text(f"❌ Service Error: {e}", color="red", size=12)

    # --- Helper: Extract Visual Assets ---
    def parse_class_visuals(class_data):
        """
        Extracts colors, images, and texts from the JSON to build a visual preview.
        """
        visuals = {
            "bg_color": class_data.get("hexBackgroundColor", "#4285f4"), # Default Google Blue
            "logo_url": None,
            "hero_url": None,
            "title": "Google Wallet Pass",
            "issuer": "Issuer Name"
        }

        # 1. Extract Logo
        if "logo" in class_data and "sourceUri" in class_data["logo"]:
            visuals["logo_url"] = class_data["logo"]["sourceUri"].get("uri")
        
        # 2. Extract Hero Image (Banner)
        if "heroImage" in class_data and "sourceUri" in class_data["heroImage"]:
            visuals["hero_url"] = class_data["heroImage"]["sourceUri"].get("uri")
        
        # 3. Extract Issuer Name
        if "localizedIssuerName" in class_data:
            visuals["issuer"] = class_data["localizedIssuerName"].get("defaultValue", {}).get("value", "Issuer")
        elif "issuerName" in class_data:
            visuals["issuer"] = class_data["issuerName"]

        # 4. Extract Title (Varies by Class Type)
        if "eventName" in class_data: # Event Ticket
            visuals["title"] = class_data["eventName"].get("defaultValue", {}).get("value")
        elif "programName" in class_data: # Loyalty
            visuals["title"] = class_data["programName"].get("defaultValue", {}).get("value")
        elif "localizedShortTitle" in class_data: # Generic
            visuals["title"] = class_data["localizedShortTitle"].get("defaultValue", {}).get("value")
        
        return visuals

    # --- UI Component: Simulated Card ---
    def build_preview_card(visuals):
        """
        Constructs a UI Container that looks like a mobile wallet pass.
        """
        # Prepare Logo Control
        logo_control = ft.Container()
        if visuals["logo_url"]:
            logo_control = ft.Image(src=visuals["logo_url"], width=50, height=50, fit=ft.ImageFit.CONTAIN, border_radius=25)
        
        # Prepare Hero Image Control
        # FIX: Changed ft.colors.BLACK12 to "black12"
        hero_control = ft.Container(height=150, bgcolor="black12", alignment=ft.alignment.center, content=ft.Text("No Hero Image", size=10))
        if visuals["hero_url"]:
            hero_control = ft.Image(src=visuals["hero_url"], width=300, height=150, fit=ft.ImageFit.COVER)

        # Build the Card Container
        return ft.Container(
            width=320, # Approximate mobile width
            bgcolor=visuals["bg_color"],
            border_radius=15,
            padding=0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE, # Clip overflow images
            # FIX: Changed ft.colors.BLACK26 to "black26"
            shadow=ft.BoxShadow(blur_radius=10, color="black26"),
            content=ft.Column([
                # Top Section: Logo & Issuer Name
                ft.Container(
                    padding=15,
                    content=ft.Row([
                        logo_control,
                        ft.Text(visuals["issuer"], color="white", weight="bold", size=14, expand=True)
                    ], alignment=ft.MainAxisAlignment.START)
                ),
                # Middle Section: Title
                ft.Container(
                    padding=ft.padding.only(left=15, right=15, bottom=10),
                    content=ft.Text(visuals["title"], color="white", size=20, weight="bold")
                ),
                # Image Section
                hero_control,
                # Bottom Mockup Section (QR & Details)
                ft.Container(
                    height=120,
                    bgcolor="white",
                    padding=15,
                    width=320,
                    content=ft.Column([
                        ft.Text("Pass Details", color="grey", size=10),
                        ft.Row([
                            ft.Icon(name="qr_code_2", size=50, color="black"),
                            ft.Column([
                                ft.Text("John Doe", weight="bold", size=14, color="black"),
                                ft.Text("1234 5678 9000", size=12, color="grey")
                            ])
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ])
                )
            ], spacing=0)
        )

    # --- Main UI Elements ---
    search_type = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="class", label="Template (Class)"),
            ft.Radio(value="object", label="User Pass (Object)")
        ]),
        value="class"
    )

    id_input = ft.TextField(
        label="ID (Suffix Only or Full ID)", 
        hint_text="e.g. Hannover96_SeasonTicket_2025_v1",
        expand=True,
        autofocus=True
    )

    # Tabs for switching views
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Visual Preview 🎨", content=ft.Container(padding=20)),
            ft.Tab(text="Raw JSON 📄", content=ft.Container(padding=20)),
        ],
        expand=True
    )

    def run_search(e):
        if not client: return
        input_val = id_input.value.strip()
        if not input_val: return

        search_btn.disabled = True
        page.update()

        try:
            # Perform Search
            if search_type.value == "class":
                data = client.get_class(input_val)
                class_part = data
            else:
                full_data = client.verify_pass(input_val)
                if "error" in full_data: raise Exception(full_data['error'])
                data = full_data
                class_part = full_data.get('class', {})

            # 1. Update JSON Tab
            json_str = json.dumps(data, indent=2)
            tabs.tabs[1].content = ft.Column([
                ft.Text("API Response:", weight="bold"),
                ft.Container(
                    content=ft.Column([ft.Text(json_str, font_family="Consolas", size=12)], scroll="auto"),
                    # FIX: Changed ft.colors.GREY_100 to "grey100"
                    bgcolor="grey100", padding=10, border_radius=5, expand=True
                )
            ], scroll="auto")

            # 2. Update Preview Tab
            visuals = parse_class_visuals(class_part)
            card = build_preview_card(visuals)
            
            tabs.tabs[0].content = ft.Container(
                content=ft.Column([
                    ft.Text("Pass Preview (Simulation)", size=16, color="grey"),
                    ft.Container(
                        content=card,
                        alignment=ft.alignment.center,
                        padding=20
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.top_center
            )
            
            # Switch to Preview Tab automatically
            tabs.selected_index = 0

        except Exception as ex:
            # FIX: Changed ft.colors.RED to "red"
            tabs.tabs[1].content = ft.Text(f"Error: {ex}", color="red")
            tabs.selected_index = 1 # Switch to JSON tab to show error
        
        search_btn.disabled = False
        page.update()

    search_btn = ft.ElevatedButton("Search", icon="search", on_click=run_search)

    page.add(
        ft.Row([ft.Icon(name="wallet"), ft.Text("Wallet Previewer", size=20, weight="bold")]),
        connection_status,
        search_type,
        ft.Row([id_input, search_btn]),
        ft.Divider(),
        tabs
    )

if __name__ == "__main__":
    ft.app(target=main)
