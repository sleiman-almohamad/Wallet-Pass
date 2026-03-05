"""
Status-message formatting helpers, shared across views.
"""

import flet as ft


def status_text(message: str, color: str = "grey", size: int = 12) -> ft.Text:
    """Create a status text control."""
    return ft.Text(message, color=color, size=size)


def set_status(control: ft.Text, message: str, color: str = "green"):
    """Convenience: update a status control in-place."""
    control.value = message
    control.color = color
