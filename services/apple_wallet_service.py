"""
Apple Wallet Service — .pkpass Generator
Generates signed .pkpass bundles without any third-party passkit library.

A .pkpass file is a ZIP archive containing:
  - pass.json        (pass definition)
  - manifest.json    (SHA-256 hashes of all files)
  - signature         (PKCS#7 detached signature of manifest.json)
  - icon.png / logo.png / strip.png … (image assets)
"""

import hashlib
import json
import os
import tempfile
import zipfile

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

import configs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download_image(url: str, dest_path: str) -> str:
    """Download *url* to *dest_path*.  Returns *dest_path* on success."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Failed to download image from {url}: {exc}") from exc

    with open(dest_path, "wb") as fh:
        fh.write(resp.content)
    return dest_path


def _hex_to_rgb(hex_color: str) -> str:
    """``#RRGGBB`` → ``rgb(R, G, B)``.  Returns white on bad input."""
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


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        """Build a signed ``.pkpass`` and return its absolute path.

        Args:
            class_data: Template-level data (logo, hero image, colours …).
            pass_data:  Object-level data (text modules, holder info …).
            object_id:  Unique identifier → serialNumber + barcode message.

        Returns:
            Absolute path to the generated ``.pkpass`` file.
        """
        # 1. Build pass.json dict
        pass_json = self._build_pass_json(class_data, pass_data, object_id)

        # 2. Collect image assets into a temp dir
        with tempfile.TemporaryDirectory(prefix="pkpass_build_") as build_dir:
            files: dict[str, bytes] = {}  # filename → raw bytes

            # pass.json
            pass_json_bytes = json.dumps(pass_json, indent=2).encode("utf-8")
            files["pass.json"] = pass_json_bytes

            # images
            self._collect_images(class_data, build_dir, files)

            # 3. Build manifest.json
            manifest = {fname: _sha256_hex(data) for fname, data in files.items()}
            manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            files["manifest.json"] = manifest_bytes

            # 4. Create PKCS#7 detached signature of manifest.json
            signature = self._sign_manifest(manifest_bytes)
            files["signature"] = signature

            # 5. Write ZIP (.pkpass)
            output_dir = tempfile.mkdtemp(prefix="pkpass_out_")
            # Clean up object_id for filename (replace dots, slashes)
            safe_id = object_id.replace("/", "_").replace(".", "_")
            output_path = os.path.join(output_dir, f"{safe_id}.pkpass")

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname, data in files.items():
                    zf.writestr(fname, data)

        return os.path.abspath(output_path)

    # ------------------------------------------------------------------
    # Internal — pass.json builder
    # ------------------------------------------------------------------

    def _build_pass_json(self, class_data: dict, pass_data: dict, object_id: str) -> dict:
        """Construct the Apple-format pass.json dictionary."""
        class_type = class_data.get("class_type", "Generic")

        # Organisation / description
        org_name = class_data.get("issuer_name") or "My Business"

        card_title_obj = class_data.get("cardTitle")
        if isinstance(card_title_obj, dict):
            description = card_title_obj.get("defaultValue", {}).get("value", org_name)
        else:
            description = card_title_obj or class_data.get("description") or org_name

        logo_text = pass_data.get("card_title") or class_data.get("card_title") or org_name

        # Colours
        bg = _hex_to_rgb(
            class_data.get("hexBackgroundColor")
            or class_data.get("base_color")
            or pass_data.get("hexBackgroundColor")
        )
        fg = _hex_to_rgb(class_data.get("hexForegroundColor", "#FFFFFF"))
        label_color = _hex_to_rgb(class_data.get("hexLabelColor", "#BBBBBB"))

        # Map class_type → Apple style key
        style_key = {
            "LoyaltyCard": "storeCard",
            "EventTicket": "eventTicket",
            "Generic": "storeCard",
        }.get(class_type, "storeCard")

        # Build fields from textModulesData
        header_fields = []
        primary_fields = []
        secondary_fields = []
        auxiliary_fields = []

        text_modules = pass_data.get("textModulesData", [])
        for idx, module in enumerate(text_modules):
            raw_key = module.get("id", f"field_{idx}")
            key = raw_key.replace(" ", "")
            field = {
                "key": key,
                "label": module.get("header", ""),
                "value": module.get("body", ""),
            }
            if idx == 0:
                primary_fields.append(field)
            elif 1 <= idx <= 3:
                secondary_fields.append(field)
            else:
                auxiliary_fields.append(field)

        # Barcode
        barcode = {
            "format": "PKBarcodeFormatQR",
            "message": object_id,
            "messageEncoding": "iso-8859-1",
        }

        pass_dict = {
            "formatVersion": 1,
            "passTypeIdentifier": self.pass_type_id,
            "teamIdentifier": self.team_id,
            "organizationName": org_name,
            "serialNumber": object_id,
            "description": description,
            "logoText": logo_text,
            "backgroundColor": bg,
            "foregroundColor": fg,
            "labelColor": label_color,
            "barcode": barcode,
            "barcodes": [barcode],
            style_key: {
                "headerFields": header_fields,
                "primaryFields": primary_fields,
                "secondaryFields": secondary_fields,
                "auxiliaryFields": auxiliary_fields,
            },
        }

        return pass_dict

    # ------------------------------------------------------------------
    # Internal — images
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_images(class_data: dict, build_dir: str, files: dict):
        """Download remote images and add their bytes to *files*."""
        # Logo / icon
        logo_url = (
            class_data.get("logo", {}).get("sourceUri", {}).get("uri")
            if isinstance(class_data.get("logo"), dict)
            else class_data.get("logo_url")
        )
        if logo_url:
            try:
                dl = _download_image(logo_url, os.path.join(build_dir, "logo_src.png"))
                img_bytes = open(dl, "rb").read()
                files["icon.png"] = img_bytes
                files["icon@2x.png"] = img_bytes
                files["logo.png"] = img_bytes
                files["logo@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach logo: {exc}")

        # Hero → strip
        hero_url = (
            class_data.get("heroImage", {}).get("sourceUri", {}).get("uri")
            if isinstance(class_data.get("heroImage"), dict)
            else class_data.get("hero_image_url")
        )
        if hero_url:
            try:
                dl = _download_image(hero_url, os.path.join(build_dir, "strip_src.png"))
                img_bytes = open(dl, "rb").read()
                files["strip.png"] = img_bytes
                files["strip@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach hero/strip image: {exc}")

    # ------------------------------------------------------------------
    # Internal — signing
    # ------------------------------------------------------------------

    def _sign_manifest(self, manifest_bytes: bytes) -> bytes:
        """Create a PKCS#7 detached (DER) signature of *manifest_bytes*."""
        # Load signing certificate
        with open(self.cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())

        # Load private key
        key_password = self.key_password.encode("utf-8") if self.key_password else None
        with open(self.key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=key_password)

        # Load WWDR intermediate certificate
        with open(self.wwdr_path, "rb") as f:
            wwdr_cert = x509.load_pem_x509_certificate(f.read())

        # Build PKCS#7 signed-data (detached, DER-encoded)
        signature = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest_bytes)
            .add_signer(cert, private_key, hashes.SHA256())
            .add_certificate(wwdr_cert)
            .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
        )

        return signature
