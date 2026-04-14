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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
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


def _sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

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
        self.wwdr_path = "certs/wwdr_g4.pem"
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
            pass_json_bytes = json.dumps(pass_json, separators=(',', ':')).encode("utf-8")
            files["pass.json"] = pass_json_bytes

            # images
            self._collect_images(class_data, pass_data, build_dir, files)

            # 3. Build manifest.json
            manifest = {fname: _sha1_hex(data) for fname, data in files.items()}
            manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode("utf-8")
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
        # Organisation / description
        org_name = pass_data.get("apple_org_name") or pass_data.get("organizationName") or "My Business"
        description = pass_data.get("apple_org_name") or pass_data.get("organizationName") or "My Business"

        logo_text = pass_data.get("apple_logo_text") or pass_data.get("logoText") or org_name

        # Colours
        bg = _hex_to_rgb(
            class_data.get("background_color")
            or class_data.get("hexBackgroundColor")
            or class_data.get("base_color")
            or pass_data.get("background_color")
            or pass_data.get("hexBackgroundColor")
        )
        fg = _hex_to_rgb(
            class_data.get("foreground_color")
            or class_data.get("hexForegroundColor")
            or pass_data.get("foreground_color")
            or "#FFFFFF"
        )
        label_color = _hex_to_rgb(
            class_data.get("label_color")
            or class_data.get("hexLabelColor")
            or pass_data.get("label_color")
            or "#BBBBBB"
        )

        # Build fields for StoreCard
        header_fields = []
        primary_fields = []
        secondary_fields = []
        auxiliary_fields = []
        back_fields = []

        dynamic_fields = pass_data.get("dynamic_fields", [])
        if dynamic_fields:
            for i, field in enumerate(dynamic_fields):
                field_type = field.get("field_type")
                field_dict = {
                    "key": f"{field_type}_{i}",
                    "label": field.get("label", ""),
                    "value": field.get("value", "")
                }
                if field_type == "header":
                    header_fields.append(field_dict)
                elif field_type == "primary":
                    primary_fields.append(field_dict)
                elif field_type == "secondary":
                    secondary_fields.append(field_dict)
                elif field_type == "auxiliary":
                    auxiliary_fields.append(field_dict)
                elif field_type == "back":
                    back_fields.append(field_dict)
        else:
            if pass_data.get("apple_header_label") or pass_data.get("apple_header_value"):
                header_fields.append({
                    "key": "header_1",
                    "label": pass_data.get("apple_header_label", ""),
                    "value": pass_data.get("apple_header_value", "")
                })

            if pass_data.get("apple_primary_label") or pass_data.get("apple_primary_value"):
                primary_fields.append({
                    "key": "primary_1",
                    "label": pass_data.get("apple_primary_label", ""),
                    "value": pass_data.get("apple_primary_value", "")
                })

            if pass_data.get("apple_sec_label") or pass_data.get("apple_sec_value"):
                secondary_fields.append({
                    "key": "secondary_1",
                    "label": pass_data.get("apple_sec_label", ""),
                    "value": pass_data.get("apple_sec_value", "")
                })

            if pass_data.get("apple_aux_label") or pass_data.get("apple_aux_value"):
                auxiliary_fields.append({
                    "key": "auxiliary_1",
                    "label": pass_data.get("apple_aux_label", ""),
                    "value": pass_data.get("apple_aux_value", "")
                })

            if pass_data.get("apple_back_label") or pass_data.get("apple_back_value"):
                back_fields.append({
                    "key": "back_1",
                    "label": pass_data.get("apple_back_label", ""),
                    "value": pass_data.get("apple_back_value", "")
                })

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
            "eventTicket": {},
        }
        
        if header_fields: pass_dict["eventTicket"]["headerFields"] = header_fields
        if primary_fields: pass_dict["eventTicket"]["primaryFields"] = primary_fields
        if secondary_fields: pass_dict["eventTicket"]["secondaryFields"] = secondary_fields
        if auxiliary_fields: pass_dict["eventTicket"]["auxiliaryFields"] = auxiliary_fields
        if back_fields: pass_dict["eventTicket"]["backFields"] = back_fields


        return pass_dict

    # ------------------------------------------------------------------
    # Internal — images
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_images(class_data: dict, pass_data: dict, build_dir: str, files: dict):
        """Download remote images and add their bytes to *files*."""
        # Logo
        logo_url = pass_data.get("apple_logo_url") or pass_data.get("logo_url") or class_data.get("logo_url")
        if logo_url:
            try:
                dl = _download_image(logo_url, os.path.join(build_dir, "logo_src.png"))
                img_bytes = open(dl, "rb").read()
                files["logo.png"] = img_bytes
                files["logo@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach logo: {exc}")

        # Mandatory icon
        icon_path = os.path.join("assets", "icon.png")
        icon_2x_path = os.path.join("assets", "icon@2x.png")
        b2f_path = os.path.join("assets", "B2F.png")
        
        # Fallback to B2F.png if icons are missing
        if not os.path.exists(icon_path) and os.path.exists(b2f_path):
            icon_path = b2f_path
        if not os.path.exists(icon_2x_path) and os.path.exists(b2f_path):
            icon_2x_path = b2f_path
            
        if os.path.exists(icon_path):
            files["icon.png"] = open(icon_path, "rb").read()
        if os.path.exists(icon_2x_path):
            files["icon@2x.png"] = open(icon_2x_path, "rb").read()

        # Hero -> strip
        strip_url = pass_data.get("apple_strip_url") or pass_data.get("strip_url") or class_data.get("hero_image_url")
        if strip_url:
            try:
                dl = _download_image(strip_url, os.path.join(build_dir, "strip_src.png"))
                img_bytes = open(dl, "rb").read()
                files["strip.png"] = img_bytes
                files["strip@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach hero/strip image: {exc}")
                
        # Background
        bg_url = pass_data.get("apple_background_image_url") or pass_data.get("background_image_url")
        if bg_url:
            try:
                dl = _download_image(bg_url, os.path.join(build_dir, "background_src.png"))
                img_bytes = open(dl, "rb").read()
                files["background.png"] = img_bytes
                files["background@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach background image: {exc}")

        # Thumbnail
        thumb_url = pass_data.get("apple_thumbnail_url") or pass_data.get("thumbnail_url")
        if thumb_url:
            try:
                dl = _download_image(thumb_url, os.path.join(build_dir, "thumbnail_src.png"))
                img_bytes = open(dl, "rb").read()
                files["thumbnail.png"] = img_bytes
                files["thumbnail@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach thumbnail image: {exc}")


    # ------------------------------------------------------------------
    # Internal — signing
    # ------------------------------------------------------------------

    def _sign_manifest(self, manifest_bytes: bytes) -> bytes:
        """Create a PKCS#7 detached (DER) signature of *manifest_bytes*."""
        import logging
        logger = logging.getLogger(__name__)
        try:
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
                
            # --- START DIAGNOSTIC LOGGING ---
            logger.info("--- Apple Wallet PKCS#7 Diagnostic ---")
            logger.info(f"Certificate Subject: {cert.subject}")
            logger.info(f"Valid After: {cert.not_valid_before_utc} | Valid Before: {cert.not_valid_after_utc}")
            
            # Cross check identifiers (UID usually holds TeamID, Subject holds PASS TYPE ID sometimes in OU)
            # The prompt warned about mismatch of teamIdentifier/passTypeIdentifier
            logger.info(f"Target Team ID: {self.team_id} | Target Pass Type ID: {self.pass_type_id}")
            logger.info("Ensure the identifiers above match the embedded Certificate Subject precisely.")
            logger.info("---------------------------------------")

            # Build PKCS#7 signed-data (detached, DER-encoded)
            signature = (
                pkcs7.PKCS7SignatureBuilder()
                .set_data(manifest_bytes)
                # Note: iOS 10+ and modern `cryptography` require SHA256 here, even if manifest is SHA1
                .add_signer(cert, private_key, hashes.SHA256())
                .add_certificate(wwdr_cert)
                .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
            )

            return signature
            
        except Exception as e:
            logger.error(f"Critical OpenSSL/Signing Error generating digital signature: {e}")
            raise
