"""
WalletPasses — Entry Point
Thin bootstrap that initialises AppState and mounts the root view.
"""

import flet as ft
from services.google_wallet_service import WalletClient
from services.api_client import APIClient
from state.app_state import AppState
from views.root_view import build_root_view


def main(page: ft.Page):
    # ── Page configuration ──
    page.title = "Google Wallet Verifier & Preview"
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.assets_dir = "assets"

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
