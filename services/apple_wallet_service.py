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
    import shutil
    if os.path.exists(url) and os.path.isfile(url):
        shutil.copy2(url, dest_path)
        return dest_path

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


# Mapping from our DB template style names → Apple's official pass.json keys
_STYLE_MAP = {
    "eventticket": "eventTicket",
    "event ticket": "eventTicket",
    "ticket": "eventTicket",
    "storecard": "storeCard",
    "store card": "storeCard",
    "coupon": "coupon",
    "boardingpass": "boardingPass",
    "boarding pass": "boardingPass",
    "generic": "generic",
}


def _map_apple_style(raw_style: str | None) -> str:
    """Convert a DB / UI pass-style string to the official Apple JSON key.

    Falls back to ``"generic"`` when the input is empty or unrecognised.
    """
    if not raw_style:
        return "generic"
    return _STYLE_MAP.get(raw_style.strip().lower(), "generic")


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
            pass_json_bytes = json.dumps(pass_json, separators=(',', ':'), ensure_ascii=False).encode("utf-8")
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
        # Priority: Template > Pass (Usually template is the brand owner)
        org_name = (class_data.get("organization_name")
                    or pass_data.get("apple_org_name")
                    or pass_data.get("organization_name")
                    or "My Business")
        description = org_name

        logo_text = (class_data.get("logo_text")
                     or pass_data.get("apple_logo_text")
                     or pass_data.get("logo_text")
                     or org_name)

        # Colours - Priority: Template > Pass
        bg = _hex_to_rgb(
            class_data.get("background_color")
            or class_data.get("hexBackgroundColor")
            or pass_data.get("background_color")
            or "#FFFFFF"
        )
        fg = _hex_to_rgb(
            class_data.get("foreground_color")
            or class_data.get("hexForegroundColor")
            or pass_data.get("foreground_color")
            or "#000000"
        )
        label_color = _hex_to_rgb(
            class_data.get("label_color")
            or class_data.get("hexLabelColor")
            or pass_data.get("label_color")
            or "#666666"
        )

        # Merge Fields Logic:
        # Template provides the structure (Labels, Types, Keys).
        # Pass provides the data (Values).
        # If Pass has a field with same key, it overrides the value.
        # If Template has a new field, it is added.
        
        template_fields_list = class_data.get("fields", [])
        pass_fields_list = pass_data.get("fields") or pass_data.get("dynamic_fields", [])
        
        # key -> {label, value, type}
        merged_fields_map = {}
        
        # 1. Start with Template fields
        for f in template_fields_list:
            ftype = f.get("field_type") or f.get("type")
            if not ftype: continue
            key = f.get("key") or f"{ftype}_{len(merged_fields_map)}"
            merged_fields_map[key] = {
                "key": key,
                "label": f.get("label", ""),
                "value": f.get("value", ""),
                "type": ftype
            }
            
        # 2. Overlay Pass fields (preserve template labels, use pass values)
        for f in pass_fields_list:
            ftype = f.get("field_type") or f.get("type")
            key = f.get("key")
            if not key: continue
            
            if key in merged_fields_map:
                # Use Template's label but Pass's value
                merged_fields_map[key]["value"] = f.get("value", "")
            else:
                # Add unique pass fields (like 'holder_name' if added manually)
                merged_fields_map[key] = {
                    "key": key,
                    "label": f.get("label", ""),
                    "value": f.get("value", ""),
                    "type": ftype or "back"
                }

        header_fields = []
        primary_fields = []
        secondary_fields = []
        auxiliary_fields = []
        back_fields = []

        import re
        for f_key, f in merged_fields_map.items():
            ftype = f["type"]
            f_val = f["value"]
            f_label = f["label"]

            # Process links ONLY for backFields as Apple doesn't support HTML elsewhere
            if ftype == "back" and isinstance(f_val, str):
                # 1. Markdown style: [Click Here](https://link.com) or [Click](link.com) -> <a href="...">Click Here</a>
                def _md_to_html(match):
                    text = match.group(1)
                    url = match.group(2)
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"
                    return f"<a href='{url}'>{text}</a>"
                
                f_val = re.sub(r'\[([^\]]+)\]\s*\(\s*([^\s\)]+)\s*\)', _md_to_html, f_val)
                
                # 2. Check for manual/auto-hyperlink (Single raw URL)
                # If the value is ONLY a URL, wrap it with the field label for a cleaner look
                if f_val.strip().startswith(("http://", "https://", "www.")) and "<a href" not in f_val:
                    raw_url = f_val.strip()
                    if raw_url.startswith("www."):
                        raw_url = f"https://{raw_url}"
                    display_text = f_label if f_label and f_label.strip() else "Open Link"
                    f_val = f"<a href='{raw_url}'>{display_text}</a>"

            field_dict = {
                "key": f["key"],
                "label": f_label,
                "value": f_val
            }
            if ftype == "header": header_fields.append(field_dict)
            elif ftype == "primary": primary_fields.append(field_dict)
            elif ftype == "secondary": secondary_fields.append(field_dict)
            elif ftype == "auxiliary": auxiliary_fields.append(field_dict)
            elif ftype == "back": back_fields.append(field_dict)

        # User request: first secondary field label gets holder name
        holder_name = pass_data.get("holder_name")
        if holder_name and secondary_fields:
            secondary_fields[0]["label"] = holder_name

        # Barcode
        barcode = {
            "format": "PKBarcodeFormatQR",
            "message": object_id,
            "messageEncoding": "iso-8859-1",
        }

        # ----- Resolve Apple Style Key from Template -----
        # 1. Try class_data (already passed by caller)
        raw_style = class_data.get("pass_style")

        # 2. If missing, look up the template from the database
        if not raw_style:
            template_id = class_data.get("template_id")
            if template_id:
                try:
                    from database.db_manager import DatabaseManager
                    _db = DatabaseManager()
                    tpl = _db.get_apple_template(template_id)
                    if tpl:
                        raw_style = tpl.get("pass_style")
                except Exception:
                    pass  # Fallback to generic if DB lookup fails

        style = _map_apple_style(raw_style)
        
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
            style: {},
            "webServiceURL": configs.APPLE_WEB_SERVICE_URL,
            "authenticationToken": pass_data.get("auth_token", ""),
        }
        
        if header_fields: pass_dict[style]["headerFields"] = header_fields
        if primary_fields: pass_dict[style]["primaryFields"] = primary_fields
        if secondary_fields: pass_dict[style]["secondaryFields"] = secondary_fields
        
        # Inject Admin Message (Notification Channel) into auxiliaryFields
        # ONLY if there is a specific admin message set in the pass data
        admin_msg_val = pass_data.get("admin_message")
        
        if admin_msg_val and admin_msg_val.strip():
            # Explicitly format the message: "Organization name : message value"
            formatted_message = f"{org_name} : {admin_msg_val}"

            # Notification
            if auxiliary_fields:
                # Replace the value of the first auxiliary field
                auxiliary_fields[0]["value"] = formatted_message
                # Using "%@" ensures the notification matches the value exactly
                auxiliary_fields[0]["changeMessage"] = "%@" 
            else:
                notif_field = {
                    "key": "admin_message",
                    "label": " ",
                    "value": formatted_message,
                    "changeMessage": "%@" 
                }
                auxiliary_fields.append(notif_field)
        
        if auxiliary_fields: pass_dict[style]["auxiliaryFields"] = auxiliary_fields
        if back_fields: pass_dict[style]["backFields"] = back_fields

        return pass_dict

    # ------------------------------------------------------------------
    # Internal — images
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_images(class_data: dict, pass_data: dict, build_dir: str, files: dict):
        """Download remote images and add their bytes to *files*."""
        # Logo - Priority: Template > Pass
        logo_url = (class_data.get("logo_url") 
                    or pass_data.get("apple_logo_url") 
                    or pass_data.get("logo_url"))
        
        if logo_url:
            try:
                dl = _download_image(logo_url, os.path.join(build_dir, "logo_src.png"))
                
                # Pillow automation for icons
                try:
                    from PIL import Image
                    with Image.open(dl) as img:
                        img = img.convert("RGBA")
                        icon_path = os.path.join(build_dir, "icon_gen.png")
                        icon2x_path = os.path.join(build_dir, "icon_gen@2x.png")
                        img.resize((29, 29), Image.Resampling.LANCZOS).save(icon_path, "PNG")
                        img.resize((58, 58), Image.Resampling.LANCZOS).save(icon2x_path, "PNG")
                        files["icon.png"] = open(icon_path, "rb").read()
                        files["icon@2x.png"] = open(icon2x_path, "rb").read()
                except Exception as p_err:
                    print(f"Warning: Pillow auto-generation failed: {p_err}")

                img_bytes = open(dl, "rb").read()
                files["logo.png"] = img_bytes
                files["logo@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach logo: {exc}")

        # Mandatory icon backup
        icon_path = os.path.join("assets", "icon.png")
        icon_2x_path = os.path.join("assets", "icon@2x.png")
        b2f_path = os.path.join("assets", "B2F.png")
        
        if not os.path.exists(icon_path) and os.path.exists(b2f_path):
            icon_path = b2f_path
        if not os.path.exists(icon_2x_path) and os.path.exists(b2f_path):
            icon_2x_path = b2f_path
            
        if "icon.png" not in files and os.path.exists(icon_path):
            files["icon.png"] = open(icon_path, "rb").read()
        if "icon@2x.png" not in files and os.path.exists(icon_2x_path):
            files["icon@2x.png"] = open(icon_2x_path, "rb").read()

        # Hero -> strip - Priority: Template > Pass
        strip_url = (class_data.get("strip_url") 
                     or class_data.get("hero_image_url")
                     or pass_data.get("apple_strip_url") 
                     or pass_data.get("strip_url"))
        
        if strip_url:
            try:
                dl = _download_image(strip_url, os.path.join(build_dir, "strip_src.png"))
                img_bytes = open(dl, "rb").read()
                files["strip.png"] = img_bytes
                files["strip@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach hero/strip image: {exc}")
                
        # Background - Priority: Template > Pass
        bg_url = (class_data.get("background_image_url")
                  or pass_data.get("apple_background_image_url") 
                  or pass_data.get("background_image_url"))
        
        if bg_url:
            try:
                dl = _download_image(bg_url, os.path.join(build_dir, "background_src.png"))
                img_bytes = open(dl, "rb").read()
                files["background.png"] = img_bytes
                files["background@2x.png"] = img_bytes
            except ValueError as exc:
                print(f"Warning: Could not attach background image: {exc}")

        # Thumbnail - Priority: Template > Pass
        thumb_url = (class_data.get("thumbnail_url")
                     or pass_data.get("apple_thumbnail_url") 
                     or pass_data.get("thumbnail_url"))
        
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

    # ------------------------------------------------------------------
    # APNs Integration
    # ------------------------------------------------------------------

    def send_push_notification(self, serial_number: str) -> dict:
        """
        Send a silent push notification to all Apple devices registered for this pass.
        Uses APNs via HTTP/2.
        """
        from database.db_manager import DatabaseManager
        import httpx
        import traceback
        import logging
        
        log = logging.getLogger(__name__)
        db = DatabaseManager()
        push_tokens = db.get_registered_devices_for_pass(serial_number)
        
        if not push_tokens:
            log.info(f"No devices registered for pass {serial_number}")
            return {"status": "success", "sent": 0, "failed": 0}
            
        success_count = 0
        failure_count = 0
        apns_host = "api.push.apple.com" 
        
        payload = "{}"
        headers = {
            "apns-topic": self.pass_type_id,
            "apns-push-type": "background",
            "apns-priority": "5",  # Must be 5 for background push-type (10 is rejected)
        }
        
        cert_tuple = (self.cert_path, self.key_path)
        
        try:
            # Use with to ensure HTTP/2 client is closed
            with httpx.Client(http2=True, cert=cert_tuple, verify=True) as client:
                for token in push_tokens:
                    try:
                        url = f"https://{apns_host}/3/device/{token}"
                        response = client.post(url, headers=headers, content=payload.encode())
                        
                        if response.status_code == 200:
                            success_count += 1
                            log.info(f"✅ APNs sent successfully to {token[:10]}...")
                        else:
                            failure_count += 1
                            log.error(f"❌ APNs failed for token {token[:10]}. Status: {response.status_code}, Body: {response.text}")
                            if response.status_code == 410 or "Unregistered" in response.text:
                                log.info(f"Token unregistered. Removing from DB: {token}")
                                db.unregister_apple_device_by_token(token)
                                
                    except Exception as e:
                        failure_count += 1
                        log.error(f"❌ Error sending APNs to {token[:10]}: {str(e)}")
                        
        except Exception as e:
            log.error(f"Failed to setup HTTP/2 client for APNs: {e}")
            return {"status": "error", "message": f"HTTP/2 Client setup failed: {str(e)}"}
            
        return {
            "status": "success",
            "sent": success_count,
            "failed": failure_count
        }

    def send_apple_template_notification(self, template_id: str, message: str = "") -> dict:
        """
        Propagate template field changes to all child passes, then send
        push notifications so devices fetch the updated .pkpass.
        """
        from database.db_manager import DatabaseManager
        import logging
        log = logging.getLogger(__name__)

        db = DatabaseManager()

        # 1. Fetch the latest template data (including updated fields)
        template = db.get_apple_template(template_id)
        template_fields = template.get("fields", []) if template else []

        passes = db.get_passes_by_apple_template(template_id)
        log.info(f"APPLE: Propagating template '{template_id}' to {len(passes)} passes "
                 f"({len(template_fields)} template fields)")

        results = {"status": "success", "sent": 0, "failed": 0}
        for p in passes:
            serial = p['serial_number']

            # 2. Propagate template fields → pass fields (labels + values)
            #    Preserve pass-specific fields not present in the template
            if template_fields:
                # Get current pass fields so we can preserve pass-only extras
                full_pass = db.get_apple_pass(serial)
                pass_fields = full_pass.get("fields", []) if full_pass else []

                # Build a set of template field keys
                template_keys = set()
                propagated = []
                for f in template_fields:
                    key = f.get("key") or f.get("field_key")
                    template_keys.add(key)
                    propagated.append({
                        "field_type": f.get("field_type") or f.get("type"),
                        "key": key,
                        "label": f.get("label", ""),
                        "value": f.get("value", ""),
                    })

                # Append pass-only fields (keys not in template) e.g. custom back links
                for pf in pass_fields:
                    pf_key = pf.get("key")
                    if pf_key and pf_key not in template_keys:
                        propagated.append({
                            "field_type": pf.get("field_type"),
                            "key": pf_key,
                            "label": pf.get("label", ""),
                            "value": pf.get("value", ""),
                        })

                db.update_apple_pass(serial, dynamic_fields=propagated)
                log.info(f"  ↳ Propagated {len(propagated)} fields to pass {serial}")

            # 3. Propagate template-level visual data (colors, images, org name)
            if template:
                visual_updates = {}
                for attr in ["background_color", "foreground_color", "label_color",
                             "organization_name", "logo_text", "logo_url",
                             "icon_url", "strip_url"]:
                    val = template.get(attr)
                    if val is not None:
                        visual_updates[attr] = val
                if visual_updates:
                    db.update_apple_pass(serial, **visual_updates)

            # 4. Clear any specific admin_message so the pass shows the latest template field values
            db.update_apple_pass_message(serial, "")

            # 5. Send APNs push so the device fetches the new .pkpass
            res = self.send_push_notification(serial)
            if res.get("status") == "success":
                results["sent"] += res.get("sent", 0)
                results["failed"] += res.get("failed", 0)

        return results
