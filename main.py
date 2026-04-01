"""
WalletPasses — Entry Point
Thin bootstrap that initialises AppState and mounts the root view.
"""

import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")
os.environ["GDK_BACKEND"] = "x11"
import flet as ft
from services.google_wallet_service import WalletClient
from services.api_client import APIClient
from state.app_state import AppState
from views.root_view import build_root_view


def main(page: ft.Page):
    # ── Page configuration ──
    page.title = "Wallet Pass Management Suite"
    page.window.width = 1440
    page.window.height = 920
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#f5f5f7"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.assets_dir = "assets"
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"}
    page.theme = ft.Theme(font_family="Inter")

    # ── Initialise services ──
    wallet_client = None
    try:
        wallet_client = WalletClient()
    except Exception as e:
        print(f"⚠️  WalletClient init failed: {e}")

    api_client = APIClient()

    # ── Initialise application state ──
    state = AppState(page, api_client, wallet_client)

    # ── Build and mount the UI ──
    controls = build_root_view(page, state)
    for control in controls:
        page.add(control)


if __name__ == "__main__":
    ft.app(target=main)
