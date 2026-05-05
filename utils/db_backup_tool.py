"""
Database Backup Tool
Export / Import all wallet pass data as a JSON file.
Database-agnostic via SQLAlchemy ORM.
"""

import json
from datetime import datetime
from typing import Tuple

from database.models import (
    SessionLocal,
    ClassesTable, GenericClassFields, GenericClassTextModuleRows,
    EventTicketClassFields, LoyaltyClassFields, TransitClassFields,
    PassesTable, EventTicketFields, GenericFields,
    PassTextModules, PassMessages,
    NotificationsTable,
    ApplePassesTemplate, AppleTemplateFields, ApplePassesData, ApplePassFields,
    AppleNotificationsTable, AppleDeviceRegistrations,
    QRCampaigns
)


def _ts(val) -> str | None:
    """Safely convert a datetime/timestamp to ISO string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


class DatabaseBackupTool:
    """Export and import the entire database as JSON."""

    def __init__(self):
        pass  # uses SessionLocal directly

    # ------------------------------------------------------------------ #
    #  EXPORT
    # ------------------------------------------------------------------ #

    def export_to_json(self, filepath: str) -> Tuple[bool, str]:
        """Serialize every table into *filepath* as JSON."""
        try:
            session = SessionLocal()
            try:
                data = self._build_export_dict(session)
            finally:
                session.close()

            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False, default=str)

            total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
            return True, f"Backup saved – {total} records exported."
        except Exception as exc:
            return False, f"Backup failed: {exc}"

    def _build_export_dict(self, session) -> dict:
        """Query all tables and return a nested dict."""
        # --- Google Classes ---
        classes = []
        for c in session.query(ClassesTable).all():
            entry = {
                "class_id": c.class_id,
                "class_type": c.class_type,
                "issuer_name": c.issuer_name,
                "base_color": c.base_color,
                "logo_url": c.logo_url,
                "hero_image_url": c.hero_image_url,
                "created_at": _ts(c.created_at),
                "updated_at": _ts(c.updated_at),
            }
            # Child: Generic
            if c.generic_fields:
                gf = c.generic_fields
                entry["generic_fields"] = {
                    "header": gf.header,
                    "subheader": gf.subheader,
                    "card_title": gf.card_title,
                    "barcode_value": gf.barcode_value,
                    "barcode_alt_text": gf.barcode_alt_text,
                    "text_module_rows": [
                        {
                            "row_index": r.row_index,
                            "left_header": r.left_header, "left_body": r.left_body, "left_type": r.left_type,
                            "middle_header": r.middle_header, "middle_body": r.middle_body, "middle_type": r.middle_type,
                            "right_header": r.right_header, "right_body": r.right_body, "right_type": r.right_type,
                        }
                        for r in gf.text_module_rows
                    ],
                }
            # Child: EventTicket
            if c.event_ticket_fields:
                ef = c.event_ticket_fields
                entry["event_ticket_fields"] = {
                    "event_name": ef.event_name,
                    "venue_name": ef.venue_name,
                    "venue_address": ef.venue_address,
                    "event_start": ef.event_start,
                }
            # Child: Loyalty
            if c.loyalty_fields:
                entry["loyalty_fields"] = {"program_name": c.loyalty_fields.program_name}
            # Child: Transit
            if c.transit_fields:
                tf = c.transit_fields
                entry["transit_fields"] = {
                    "transit_type": tf.transit_type,
                    "transit_operator_name": tf.transit_operator_name,
                }
            classes.append(entry)

        # --- Google Passes ---
        passes = []
        for p in session.query(PassesTable).all():
            entry = {
                "object_id": p.object_id,
                "class_id": p.class_id,
                "holder_name": p.holder_name,
                "holder_email": p.holder_email,
                "status": p.status,
                "sync_status": p.sync_status,
                "last_synced_at": _ts(p.last_synced_at),
                "created_at": _ts(p.created_at),
                "updated_at": _ts(p.updated_at),
            }
            if p.generic_fields:
                gf = p.generic_fields
                entry["generic_fields"] = {
                    "header_value": gf.header_value,
                    "subheader_value": gf.subheader_value,
                    "card_title": gf.card_title,
                    "logo_url": gf.logo_url,
                    "hero_image_url": gf.hero_image_url,
                    "hex_background_color": gf.hex_background_color,
                    "barcode_type": gf.barcode_type,
                    "barcode_value": gf.barcode_value,
                    "barcode_alt_text": gf.barcode_alt_text,
                }
            if p.event_ticket_fields:
                et = p.event_ticket_fields
                entry["event_ticket_fields"] = {
                    "ticket_holder_name": et.ticket_holder_name,
                    "confirmation_code": et.confirmation_code,
                    "seat": et.seat,
                    "section": et.section,
                    "gate": et.gate,
                }
            if p.text_modules:
                entry["text_modules"] = [
                    {
                        "module_id": m.module_id,
                        "header": m.header,
                        "body": m.body,
                        "module_type": m.module_type,
                        "display_order": m.display_order,
                    }
                    for m in p.text_modules
                ]
            if p.messages:
                entry["messages"] = [
                    {
                        "message_id": m.message_id,
                        "header": m.header,
                        "body": m.body,
                        "message_type": m.message_type,
                        "start_date": m.start_date,
                        "end_date": m.end_date,
                    }
                    for m in p.messages
                ]
            passes.append(entry)

        # --- Google Notifications ---
        notifications = [
            {
                "id": n.id,
                "class_id": n.class_id,
                "object_id": n.object_id,
                "event_type": n.event_type,
                "status": n.status,
                "message": n.message,
                "created_at": _ts(n.created_at),
            }
            for n in session.query(NotificationsTable).all()
        ]        # --- Apple Passes ---
        apple_passes = []
        for p in session.query(ApplePassesData).all():
            entry = self._apple_pass_to_dict(p)
            apple_passes.append(entry)

        # --- Apple Templates ---
        apple_templates = []
        for t in session.query(ApplePassesTemplate).all():
            entry = {
                "template_id": t.template_id,
                "template_name": t.template_name,
                "pass_style": t.pass_style,
                "pass_type_identifier": t.pass_type_identifier,
                "team_identifier": t.team_identifier,
                "background_color": t.background_color,
                "foreground_color": t.foreground_color,
                "label_color": t.label_color,
                "logo_text": t.logo_text,
                "organization_name": t.organization_name,
                "logo_url": t.logo_url,
                "icon_url": t.icon_url,
                "strip_url": t.strip_url,
                "background_image_url": t.background_image_url,
                "thumbnail_url": t.thumbnail_url,
                "barcode_value": t.barcode_value,
                "barcode_alt_text": t.barcode_alt_text,
                "created_at": _ts(t.created_at),
                "updated_at": _ts(t.updated_at),
                "fields": [
                    {
                        "type": f.field_type,
                        "key": f.field_key,
                        "label": f.label,
                        "value": f.value
                    }
                    for f in t.fields
                ]
            }
            apple_templates.append(entry)

        # --- Apple Notifications ---
        apple_notifications = [
            {
                "id": n.id,
                "pass_type_id": n.pass_type_id,
                "serial_number": n.serial_number,
                "status": n.status,
                "message": n.message,
                "created_at": _ts(n.created_at),
            }
            for n in session.query(AppleNotificationsTable).all()
        ]

        # --- Apple Device Registrations ---
        apple_device_registrations = [
            {
                "id": r.id,
                "device_library_id": r.device_library_id,
                "push_token": r.push_token,
                "serial_number": r.serial_number,
                "pass_type_id": r.pass_type_id,
                "created_at": _ts(r.created_at),
            }
            for r in session.query(AppleDeviceRegistrations).all()
        ]

        # --- QR Campaigns ---
        qr_campaigns = [
            {
                "id": c.id,
                "campaign_name": c.campaign_name,
                "slug": c.slug,
                "google_class_id": c.google_class_id,
                "apple_template_id": c.apple_template_id,
                "landing_title": c.landing_title,
                "landing_subtitle": c.landing_subtitle,
                "is_active": c.is_active,
                "created_at": _ts(c.created_at),
                "updated_at": _ts(c.updated_at),
            }
            for c in session.query(QRCampaigns).all()
        ]

        return {
            "backup_version": 3, # Updated to 3 for new schema
            "exported_at": datetime.now().isoformat(),
            "classes": classes,
            "passes": passes,
            "notifications": notifications,
            "apple_templates": apple_templates,
            "apple_passes": apple_passes,
            "apple_notifications": apple_notifications,
            "apple_device_registrations": apple_device_registrations,
            "qr_campaigns": qr_campaigns,
        }

    def _apple_pass_to_dict(self, p: ApplePassesData) -> dict:
        d = {
            "pass_id": p.pass_id,
            "template_id": p.template_id,
            "holder_name": p.holder_name,
            "holder_email": p.holder_email,
            "status": p.status,
            "auth_token": p.auth_token,
            "background_color": p.background_color,
            "foreground_color": p.foreground_color,
            "label_color": p.label_color,
            "organization_name": p.organization_name,
            "logo_text": p.logo_text,
            "logo_url": p.logo_url,
            "icon_url": p.icon_url,
            "strip_url": p.strip_url,
            "background_image_url": p.background_image_url,
            "thumbnail_url": p.thumbnail_url,
            "barcode_value": p.barcode_value,
            "barcode_alt_text": p.barcode_alt_text,
            "ticket_layout": p.ticket_layout,
            "admin_message": p.admin_message,
            "created_at": _ts(p.created_at),
            "updated_at": _ts(p.updated_at),
            "fields": [
                {
                    "type": f.field_type,
                    "key": f.field_key,
                    "label": f.label,
                    "value": f.value
                }
                for f in p.fields
            ]
        }
        return d

    # ------------------------------------------------------------------ #
    #  IMPORT
    # ------------------------------------------------------------------ #

    def import_from_json(self, filepath: str) -> Tuple[bool, str]:
        """Read *filepath* and restore every table."""
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            session = SessionLocal()
            try:
                self._restore_from_dict(session, data)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

            total = sum(
                len(data.get(k, []))
                for k in ("classes", "passes", "notifications",
                          "apple_templates", "apple_passes", 
                          "apple_notifications", "apple_device_registrations",
                          "qr_campaigns")
            )
            return True, f"Restore complete – {total} records imported."
        except Exception as exc:
            return False, f"Restore failed: {exc}"

    def _restore_from_dict(self, session, data: dict):
        """Insert / merge rows respecting FK order."""
        if "apple_classes" in data:
            print("Notice: Ignoring deprecated 'apple_classes' from legacy backup.")

        # ── 1. Google Classes ──
        for c in data.get("classes", []):
            cls = ClassesTable(
                class_id=c["class_id"],
                class_type=c.get("class_type", "Generic"),
                issuer_name=c.get("issuer_name"),
                base_color=c.get("base_color"),
                logo_url=c.get("logo_url"),
                hero_image_url=c.get("hero_image_url"),
                created_at=datetime.fromisoformat(c["created_at"]) if c.get("created_at") else None,
                updated_at=datetime.fromisoformat(c["updated_at"]) if c.get("updated_at") else None,
            )
            session.merge(cls)
            session.flush()

            # Child: Generic
            gf = c.get("generic_fields")
            if gf:
                session.merge(GenericClassFields(
                    class_id=c["class_id"],
                    header=gf.get("header"),
                    subheader=gf.get("subheader"),
                    card_title=gf.get("card_title"),
                    barcode_value=gf.get("barcode_value"),
                    barcode_alt_text=gf.get("barcode_alt_text"),
                ))
                session.flush()

                # Text module rows – clear first, then insert
                session.query(GenericClassTextModuleRows).filter_by(
                    class_id=c["class_id"]
                ).delete()
                session.flush()
                for row in gf.get("text_module_rows", []):
                    session.add(GenericClassTextModuleRows(
                        class_id=c["class_id"],
                        row_index=row.get("row_index", 0),
                        left_header=row.get("left_header"),
                        left_body=row.get("left_body"),
                        left_type=row.get("left_type", "text"),
                        middle_header=row.get("middle_header"),
                        middle_body=row.get("middle_body"),
                        middle_type=row.get("middle_type", "text"),
                        right_header=row.get("right_header"),
                        right_body=row.get("right_body"),
                        right_type=row.get("right_type", "text"),
                    ))

            # Child: EventTicket
            ef = c.get("event_ticket_fields")
            if ef:
                session.merge(EventTicketClassFields(
                    class_id=c["class_id"],
                    event_name=ef.get("event_name"),
                    venue_name=ef.get("venue_name"),
                    venue_address=ef.get("venue_address"),
                    event_start=ef.get("event_start"),
                ))

            # Child: Loyalty
            lf = c.get("loyalty_fields")
            if lf:
                session.merge(LoyaltyClassFields(
                    class_id=c["class_id"],
                    program_name=lf.get("program_name"),
                ))

            # Child: Transit
            tf = c.get("transit_fields")
            if tf:
                session.merge(TransitClassFields(
                    class_id=c["class_id"],
                    transit_type=tf.get("transit_type"),
                    transit_operator_name=tf.get("transit_operator_name"),
                ))

        # ── 2. Google Passes ──
        for p in data.get("passes", []):
            pass_obj = PassesTable(
                object_id=p["object_id"],
                class_id=p["class_id"],
                holder_name=p.get("holder_name", ""),
                holder_email=p.get("holder_email", ""),
                status=p.get("status", "Active"),
                sync_status=p.get("sync_status", "pending"),
                created_at=datetime.fromisoformat(p["created_at"]) if p.get("created_at") else None,
                updated_at=datetime.fromisoformat(p["updated_at"]) if p.get("updated_at") else None,
            )
            session.merge(pass_obj)
            session.flush()

            # Child: Generic
            gf = p.get("generic_fields")
            if gf:
                session.merge(GenericFields(
                    object_id=p["object_id"],
                    header_value=gf.get("header_value"),
                    subheader_value=gf.get("subheader_value"),
                    card_title=gf.get("card_title"),
                    logo_url=gf.get("logo_url"),
                    hero_image_url=gf.get("hero_image_url"),
                    hex_background_color=gf.get("hex_background_color"),
                    barcode_type=gf.get("barcode_type"),
                    barcode_value=gf.get("barcode_value"),
                    barcode_alt_text=gf.get("barcode_alt_text"),
                ))

            # Child: EventTicket
            et = p.get("event_ticket_fields")
            if et:
                session.merge(EventTicketFields(
                    object_id=p["object_id"],
                    ticket_holder_name=et.get("ticket_holder_name"),
                    confirmation_code=et.get("confirmation_code"),
                    seat=et.get("seat"),
                    section=et.get("section"),
                    gate=et.get("gate"),
                ))

            # Child: Text modules – clear + re-insert
            session.query(PassTextModules).filter_by(
                object_id=p["object_id"]
            ).delete()
            session.flush()
            for tm in p.get("text_modules", []):
                session.add(PassTextModules(
                    object_id=p["object_id"],
                    module_id=tm.get("module_id"),
                    header=tm.get("header"),
                    body=tm.get("body"),
                    module_type=tm.get("module_type", "text"),
                    display_order=tm.get("display_order", 0),
                ))

            # Child: Messages – clear + re-insert
            session.query(PassMessages).filter_by(
                object_id=p["object_id"]
            ).delete()
            session.flush()
            for msg in p.get("messages", []):
                session.add(PassMessages(
                    object_id=p["object_id"],
                    message_id=msg.get("message_id"),
                    header=msg.get("header"),
                    body=msg.get("body"),
                    message_type=msg.get("message_type"),
                    start_date=msg.get("start_date"),
                    end_date=msg.get("end_date"),
                ))

        # ── 3. Google Notifications (append only — no merge on auto-id) ──
        existing_notif_ids = {
            n.id for n in session.query(NotificationsTable.id).all()
        }
        for n in data.get("notifications", []):
            if n.get("id") not in existing_notif_ids:
                session.add(NotificationsTable(
                    class_id=n.get("class_id"),
                    object_id=n.get("object_id"),
                    event_type=n.get("event_type", "custom_message"),
                    status=n.get("status", "Sent"),
                    message=n.get("message"),
                    created_at=datetime.fromisoformat(n["created_at"]) if n.get("created_at") else datetime.now(),
                ))

        # ── 4. Apple Templates ──
        for t in data.get("apple_templates", []):
            session.merge(ApplePassesTemplate(
                template_id=t["template_id"],
                template_name=t.get("template_name", ""),
                pass_style=t.get("pass_style", "storeCard"),
                pass_type_identifier=t.get("pass_type_identifier", ""),
                team_identifier=t.get("team_identifier", ""),
                background_color=t.get("background_color"),
                foreground_color=t.get("foreground_color"),
                label_color=t.get("label_color"),
                logo_text=t.get("logo_text"),
                organization_name=t.get("organization_name"),
                logo_url=t.get("logo_url"),
                icon_url=t.get("icon_url"),
                strip_url=t.get("strip_url"),
                background_image_url=t.get("background_image_url"),
                thumbnail_url=t.get("thumbnail_url"),
                barcode_value=t.get("barcode_value"),
                barcode_alt_text=t.get("barcode_alt_text"),
                created_at=datetime.fromisoformat(t["created_at"]) if t.get("created_at") else None,
                updated_at=datetime.fromisoformat(t["updated_at"]) if t.get("updated_at") else None,
            ))
            session.flush()
            # Child Fields
            session.query(AppleTemplateFields).filter_by(template_id=t["template_id"]).delete()
            for f in t.get("fields", []):
                session.add(AppleTemplateFields(
                    template_id=t["template_id"],
                    field_type=f["type"],
                    field_key=f.get("key", ""),
                    label=f.get("label"),
                    value=f["value"]
                ))
        session.flush()

        # ── 5. Apple Passes ──
        for p in data.get("apple_passes", []):
            session.merge(ApplePassesData(
                pass_id=p["pass_id"],
                template_id=p["template_id"],
                holder_name=p.get("holder_name", ""),
                holder_email=p.get("holder_email", ""),
                status=p.get("status", "Active"),
                auth_token=p.get("auth_token", ""),
                background_color=p.get("background_color"),
                foreground_color=p.get("foreground_color"),
                label_color=p.get("label_color"),
                organization_name=p.get("organization_name"),
                logo_text=p.get("logo_text"),
                logo_url=p.get("logo_url"),
                icon_url=p.get("icon_url"),
                strip_url=p.get("strip_url"),
                background_image_url=p.get("background_image_url"),
                thumbnail_url=p.get("thumbnail_url"),
                barcode_value=p.get("barcode_value"),
                barcode_alt_text=p.get("barcode_alt_text"),
                ticket_layout=p.get("ticket_layout", "strip"),
                admin_message=p.get("admin_message"),
                created_at=datetime.fromisoformat(p["created_at"]) if p.get("created_at") else None,
                updated_at=datetime.fromisoformat(p["updated_at"]) if p.get("updated_at") else None,
            ))
            session.flush()
            # Child Fields
            session.query(ApplePassFields).filter_by(pass_id=p["pass_id"]).delete()
            for f in p.get("fields", []):
                session.add(ApplePassFields(
                    pass_id=p["pass_id"],
                    field_type=f["type"],
                    field_key=f.get("key", ""),
                    label=f.get("label"),
                    value=f["value"]
                ))
        session.flush()

        # ── 6. Apple Notifications (append only) ──
        existing_apple_notif_ids = {
            n.id for n in session.query(AppleNotificationsTable.id).all()
        }
        for n in data.get("apple_notifications", []):
            if n.get("id") not in existing_apple_notif_ids:
                session.add(AppleNotificationsTable(
                    pass_type_id=n.get("pass_type_id"),
                    serial_number=n.get("serial_number"),
                    status=n.get("status", "Sent"),
                    message=n.get("message"),
                    created_at=datetime.fromisoformat(n["created_at"]) if n.get("created_at") else datetime.now(),
                ))

        # ── 7. Apple Device Registrations (append only) ──
        existing_reg_ids = {
            r.id for r in session.query(AppleDeviceRegistrations.id).all()
        }
        for r in data.get("apple_device_registrations", []):
            if r.get("id") not in existing_reg_ids:
                session.add(AppleDeviceRegistrations(
                    device_library_id=r.get("device_library_id", ""),
                    push_token=r.get("push_token", ""),
                    serial_number=r.get("serial_number", ""),
                    pass_type_id=r.get("pass_type_id", ""),
                    created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else datetime.now(),
                ))

        # ── 8. QR Campaigns ──
        for c in data.get("qr_campaigns", []):
            session.merge(QRCampaigns(
                id=c["id"],
                campaign_name=c["campaign_name"],
                slug=c["slug"],
                google_class_id=c.get("google_class_id"),
                apple_template_id=c.get("apple_template_id"),
                landing_title=c.get("landing_title"),
                landing_subtitle=c.get("landing_subtitle"),
                is_active=c.get("is_active", True),
                created_at=datetime.fromisoformat(c["created_at"]) if c.get("created_at") else None,
                updated_at=datetime.fromisoformat(c["updated_at"]) if c.get("updated_at") else None,
            ))
        session.flush()
