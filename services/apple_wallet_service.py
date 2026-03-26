"""
Apple Wallet Service — .pkpass Generator
Dynamically generates signed .pkpass files using the py-pkpass library.
Maps Google Wallet payload concepts to Apple PassKit format.
"""

import os
import tempfile
import requests

from wallet.Pass import Pass
from wallet.PassStyles import StoreCard, EventTicket, Generic
from wallet.PassProps.Barcode import Barcode
from wallet.Schemas.FieldProps import FieldProps

import configs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download_image(url: str, temp_dir: str, filename: str) -> str:
    """Download an image from *url* into *temp_dir*/*filename*.

    Returns the absolute path to the downloaded file.
    Raises ``ValueError`` if the download fails.
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Failed to download image from {url}: {exc}") from exc

    local_path = os.path.join(temp_dir, filename)
    with open(local_path, "wb") as fh:
        fh.write(resp.content)
    return local_path


def _hex_to_rgb(hex_color: str) -> str:
    """Convert ``#RRGGBB`` (or ``RRGGBB``) to ``rgb(R, G, B)``.

    The py-pkpass library expects colours in ``rgb(…)`` format.
    Returns a sensible default when conversion is not possible.
    """
    if not hex_color:
        return "rgb(255, 255, 255)"

    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "rgb(255, 255, 255)"

    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgb({r}, {g}, {b})"
    except ValueError:
        return "rgb(255, 255, 255)"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AppleWalletService:
    """Generate signed Apple Wallet ``.pkpass`` files."""

    def __init__(self):
        self.cert_path = configs.APPLE_CERT_PATH
        self.key_path = configs.APPLE_KEY_PATH
        self.wwdr_path = configs.APPLE_WWDR_PATH
        self.key_password = configs.APPLE_KEY_PASSWORD or ""
        self.team_id = configs.APPLE_TEAM_ID
        self.pass_type_id = configs.APPLE_PASS_TYPE_ID

        # Validate certificate files exist
        for label, path in [
            ("Certificate", self.cert_path),
            ("Private key", self.key_path),
            ("WWDR certificate", self.wwdr_path),
        ]:
            if not os.path.isfile(path):
                raise FileNotFoundError(
                    f"Apple Wallet {label} not found at: {path}"
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_pass(
        self,
        class_data: dict,
        pass_data: dict,
        object_id: str,
    ) -> str:
        """Build a signed ``.pkpass`` file and return its absolute path.

        Args:
            class_data: Template / class-level data (logo, hero image,
                        colours, issuer name, class type, etc.).
            pass_data:  Object-level data (text modules, holder info …).
            object_id:  Unique identifier for this pass instance.
                        Also used as the ``serialNumber`` and barcode message.

        Returns:
            Absolute path to the generated ``.pkpass`` file.
        """
        # --- 1. Determine card style --------------------------------
        class_type = class_data.get("class_type", "Generic")
        card = self._make_card(class_type)

        # --- 2. Map text modules to card fields ----------------------
        text_modules = pass_data.get("textModulesData", [])
        for idx, module in enumerate(text_modules):
            key = module.get("id", f"field_{idx}")
            value = module.get("body", "")
            label = module.get("header", "")
            field = FieldProps(key=key, value=value, label=label)

            if idx == 0:
                card.add_header_field(field)
            elif idx <= 2:
                card.add_secondary_field(field)
            else:
                card.add_auxiliary_field(field)

        # --- 3. Colours ---------------------------------------------
        bg_color = _hex_to_rgb(
            class_data.get("hexBackgroundColor")
            or pass_data.get("hexBackgroundColor")
        )
        fg_color = _hex_to_rgb(
            class_data.get("hexForegroundColor", "#FFFFFF")
        )
        label_color = _hex_to_rgb(
            class_data.get("hexLabelColor", "#BBBBBB")
        )

        # --- 4. Organisation / description --------------------------
        org_name = (
            class_data.get("issuerName")
            or class_data.get("organizationName")
            or "Organization"
        )
        description = (
            class_data.get("description")
            or class_data.get("cardTitle", {}).get("defaultValue", {}).get("value")
            or org_name
        )
        logo_text = class_data.get("logoText") or org_name

        # --- 5. Build Pass object -----------------------------------
        passfile = Pass(
            card,
            self.pass_type_id,
            self.team_id,
            org_name,
            serial_number=object_id,
            description=description,
            logo_text=logo_text,
            background_color=bg_color,
            foreground_color=fg_color,
            label_color=label_color,
            barcodes=[Barcode(message=object_id)],
        )

        # --- 6. Attach images in a temporary directory ---------------
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._attach_images(passfile, class_data, tmp_dir)

            # --- 7. Sign & write the .pkpass -------------------------
            output_dir = tempfile.mkdtemp(prefix="pkpass_")
            output_filename = os.path.join(output_dir, f"{object_id}.pkpass")

            passfile.create(
                self.cert_path,
                self.key_path,
                self.wwdr_path,
                password=self.key_password,
                file_name=output_filename,
            )

        return os.path.abspath(output_filename)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_card(class_type: str):
        """Return the correct py-pkpass card style for a Google class type."""
        mapping = {
            "LoyaltyCard": StoreCard,
            "EventTicket": EventTicket,
        }
        return mapping.get(class_type, Generic)()

    @staticmethod
    def _attach_images(passfile: Pass, class_data: dict, tmp_dir: str):
        """Download remote images and attach them to the pass file."""
        # Logo / icon --------------------------------------------------
        logo_url = (
            class_data.get("logo", {}).get("sourceUri", {}).get("uri")
            if isinstance(class_data.get("logo"), dict)
            else class_data.get("logo_url")
        )
        if logo_url:
            try:
                local_logo = _download_image(logo_url, tmp_dir, "logo_src.png")
                passfile.add_file("icon.png", open(local_logo, "rb"))
                passfile.add_file("icon@2x.png", open(local_logo, "rb"))
                passfile.add_file("logo.png", open(local_logo, "rb"))
                passfile.add_file("logo@2x.png", open(local_logo, "rb"))
            except ValueError as exc:
                print(f"Warning: Could not attach logo: {exc}")

        # Hero / strip -------------------------------------------------
        hero_url = (
            class_data.get("heroImage", {}).get("sourceUri", {}).get("uri")
            if isinstance(class_data.get("heroImage"), dict)
            else class_data.get("hero_image_url")
        )
        if hero_url:
            try:
                local_hero = _download_image(hero_url, tmp_dir, "strip_src.png")
                passfile.add_file("strip.png", open(local_hero, "rb"))
                passfile.add_file("strip@2x.png", open(local_hero, "rb"))
            except ValueError as exc:
                print(f"Warning: Could not attach hero/strip image: {exc}")
