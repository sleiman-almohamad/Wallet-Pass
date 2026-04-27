"""
WalletPasses — Entry Point
Thin bootstrap that initialises AppState and mounts the root view.
"""

import os
import subprocess
import sys
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
    # Check if we are running in a standalone process and want to enable hot reload
    
    # If run as 'python main.py' without flet CLI, re-execute with hot reload
    if len(sys.argv) == 1 and not os.getenv("FLET_APP_RELOAD_PROCESSED"):
        os.environ["FLET_APP_RELOAD_PROCESSED"] = "1"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_flet = os.path.join(current_dir, ".venv", "bin", "flet")
        bin_flet = os.path.join(os.path.dirname(sys.executable), "flet")
        
        flet_cmd = "flet"
        if os.path.exists(venv_flet):
            flet_cmd = venv_flet
        elif os.path.exists(bin_flet):
            flet_cmd = bin_flet

        print(f"🚀 Starting Flet with Hot Reload (using {flet_cmd})...")
        try:
            # Force current directory to where main.py is
            subprocess.run([flet_cmd, "run", "main.py", "--reload"], cwd=current_dir)
        except Exception as e:
            print(f"Hot reload failed to start: {e}. Falling back to standard mode.")
            ft.app(target=main)
    else:
        # Normal flet run or fallback
        ft.app(target=main)
    #ft.app(target=main, view=ft.AppView.WEB_BROWSER,port=8500)
