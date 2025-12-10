"""
Image Uploader Component
Upload and manage logo and hero images for passes
"""

import flet as ft
import os
import shutil
from pathlib import Path


class ImageUploader(ft.UserControl):
    """
    Image uploader for logo and hero images
    Supports both file upload and URL input
    """
    
    # Recommended dimensions for different image types
    DIMENSIONS = {
        "logo": {"width": 660, "height": 660, "text": "660x660 px"},
        "hero": {"width": 1032, "height": 336, "text": "1032x336 px"}
    }
    
    def __init__(self, image_type, template_state):
        """
        Args:
            image_type: "logo" or "hero"
            template_state: TemplateState instance
        """
        super().__init__()
        self.image_type = image_type
        self.template_state = template_state
        self.current_image = template_state.get(f"{image_type}_url")
        self.url_input = None
        self.file_picker = None
        
        # Create assets directory if it doesn't exist
        self.assets_dir = Path("assets/templates")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def build(self):
        """Build the image uploader UI"""
        
        # File picker (will be added to page overlay)
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked
        )
        
        # URL input
        self.url_input = ft.TextField(
            label="Or enter image URL",
            hint_text="https://example.com/image.png",
            expand=True,
            on_change=self._on_url_change
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{self.image_type.title()} Image",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    f"Recommended: {self.DIMENSIONS[self.image_type]['text']}",
                    size=11,
                    color="grey"
                ),
                ft.Container(height=5),
                
                # Upload options
                ft.Row([
                    ft.ElevatedButton(
                        "Upload File",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=self._pick_file
                    ),
                    self.url_input
                ], spacing=10),
                
                ft.Container(height=10),
                
                # Image preview
                self._build_preview(),
                
                # Clear button
                ft.TextButton(
                    "Clear Image",
                    icon=ft.icons.CLEAR,
                    on_click=self._clear_image
                ) if self.current_image else ft.Container()
                
            ], spacing=8),
            padding=15,
            border=ft.border.all(1, "grey300"),
            border_radius=10
        )
    
    def _build_preview(self):
        """Build image preview"""
        if self.current_image:
            return ft.Container(
                content=ft.Image(
                    src=self.current_image,
                    width=200,
                    height=100 if self.image_type == "hero" else 100,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=8
                ),
                bgcolor="grey100",
                padding=10,
                border_radius=8,
                alignment=ft.alignment.center
            )
        else:
            return ft.Container(
                height=100,
                bgcolor="grey100",
                border_radius=8,
                content=ft.Column([
                    ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED, size=30, color="grey"),
                    ft.Text("No image", size=12, color="grey")
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
    
    def _pick_file(self, e):
        """Open file picker"""
        if self.file_picker:
            # Add file picker to page overlay if not already added
            if self.file_picker not in self.page.overlay:
                self.page.overlay.append(self.file_picker)
                self.page.update()
            
            # Open file picker
            self.file_picker.pick_files(
                allowed_extensions=["png", "jpg", "jpeg", "webp"],
                dialog_title=f"Select {self.image_type.title()} Image"
            )
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection"""
        if e.files and len(e.files) > 0:
            file = e.files[0]
            
            # Copy file to assets directory
            try:
                source_path = Path(file.path)
                dest_filename = f"{self.image_type}_{source_path.name}"
                dest_path = self.assets_dir / dest_filename
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                
                # Update state with relative path
                image_url = str(dest_path)
                self.current_image = image_url
                self.url_input.value = ""
                self.template_state.update(f"{self.image_type}_url", image_url)
                self.update()
                
            except Exception as ex:
                print(f"Error uploading image: {ex}")
    
    def _on_url_change(self, e):
        """Handle URL input"""
        url = e.control.value.strip()
        if url:
            self.current_image = url
            self.template_state.update(f"{self.image_type}_url", url)
            self.update()
    
    def _clear_image(self, e):
        """Clear current image"""
        self.current_image = None
        self.url_input.value = ""
        self.template_state.update(f"{self.image_type}_url", None)
        self.update()
