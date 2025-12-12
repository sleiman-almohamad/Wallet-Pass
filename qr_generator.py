"""
QR Code Generator for Google Wallet Save Links
"""

import qrcode
from pathlib import Path


def generate_qr_code(url: str, filename: str, assets_dir: str = "assets") -> str:
    """
    Generate a QR code for a given URL
    
    Args:
        url: The URL to encode in the QR code
        filename: Name for the QR code file (without extension)
        assets_dir: Directory to save QR codes
        
    Returns:
        Path to the generated QR code image
    """
    # Create assets directory if it doesn't exist
    assets_path = Path(assets_dir)
    assets_path.mkdir(exist_ok=True)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to file
    qr_path = assets_path / f"{filename}.png"
    img.save(str(qr_path))
    
    return str(qr_path)
