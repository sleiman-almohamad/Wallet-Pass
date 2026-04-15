"""
Database Manager for Wallet Passes — SQLAlchemy ORM edition
Provides CRUD operations for Classes_Table, Passes_Table, and Notifications_Table
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from exceptions import DatabaseError, ValidationError

from sqlalchemy.orm import Session

from database.models import (
    SessionLocal,
    ClassesTable, GenericClassFields, GenericClassTextModuleRows, EventTicketClassFields,
    LoyaltyClassFields, TransitClassFields,
    PassesTable, EventTicketFields, GenericFields,
    PassTextModules, PassMessages,
    NotificationsTable,
    ApplePassesTemplate, ApplePassesData, ApplePassFields,
    AppleNotificationsTable, AppleDeviceRegistrations
)


class DatabaseManager:
    """Manages database operations for wallet passes using SQLAlchemy ORM"""

    def __init__(self):
        """Initialize database manager (engine/session come from models.py)"""
        pass

    @contextmanager
    def get_session(self):
        """Context manager for SQLAlchemy sessions"""
        session: Session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Database error: {e}") from e
        finally:
            session.close()

    # Keep legacy alias so any callers using get_connection still work
    get_connection = get_session

    # ========================================================================
    # Classes_Table Operations (Parent + Child Tables)
    # ========================================================================

    def create_class(self, class_id: str, class_type: str,
                     issuer_name: Optional[str] = None,
                     base_color: Optional[str] = None,
                     logo_url: Optional[str] = None,
                     hero_image_url: Optional[str] = None,
                     # Generic-specific
                     header_text: Optional[str] = None,
                     card_title: Optional[str] = None,
                     # EventTicket-specific
                     event_name: Optional[str] = None,
                     venue_name: Optional[str] = None,
                     venue_address: Optional[str] = None,
                     event_start: Optional[str] = None,
                     # Loyalty-specific
                     program_name: Optional[str] = None,
                     # Transit-specific
                     transit_type: Optional[str] = None,
                     transit_operator_name: Optional[str] = None,
                     # Generic-specific extended
                     text_module_rows: Optional[list] = None,
                     # Legacy compat (ignored for storage)
                     class_json: Optional[Dict[str, Any]] = None,
                     **extra) -> bool:
        """Create a new pass class in parent + child tables."""
        with self.get_session() as session:
            # 1. Insert parent row
            parent = ClassesTable(
                class_id=class_id, class_type=class_type,
                issuer_name=issuer_name, base_color=base_color,
                logo_url=logo_url, hero_image_url=hero_image_url,
            )
            session.add(parent)
            session.flush()

            # 2. Insert child row based on type
            if class_type == 'Generic':
                session.add(GenericClassFields(
                    class_id=class_id, header=header_text, card_title=card_title,
                ))
                session.flush()
                
                # Insert text module rows
                if text_module_rows:
                    for row in text_module_rows:
                        if hasattr(row, 'dict'):
                            row = row.dict()
                        session.add(GenericClassTextModuleRows(
                            class_id=class_id,
                            row_index=row.get('row_index', 0),
                            left_header=row.get('left_header'), left_body=row.get('left_body'),
                            middle_header=row.get('middle_header'), middle_body=row.get('middle_body'),
                            right_header=row.get('right_header'), right_body=row.get('right_body')
                        ))
            elif class_type == 'EventTicket':
                session.add(EventTicketClassFields(
                    class_id=class_id, event_name=event_name,
                    venue_name=venue_name, venue_address=venue_address,
                    event_start=event_start,
                ))
            elif class_type == 'LoyaltyCard':
                session.add(LoyaltyClassFields(
                    class_id=class_id, program_name=program_name,
                ))
            elif class_type == 'TransitPass':
                session.add(TransitClassFields(
                    class_id=class_id, transit_type=transit_type,
                    transit_operator_name=transit_operator_name,
                ))
            # GiftCard has no child table
            return True

    def _build_class_json(self, result: dict) -> dict:
        """Helper: synthesize class_json from relational columns using json_templates."""
        from core.json_templates import get_template
        class_type = result.get("class_type", "Generic")
        class_id = result.get("class_id", "")

        args = {
            "background_color": result.get("base_color"),
            "logo_url": result.get("logo_url"),
            "program_logo_url": result.get("logo_url"),
            "hero_image_url": result.get("hero_image_url"),
            "issuer_name": result.get("issuer_name"),
        }

        # Add type-specific args
        if class_type == "Generic":
            args["header_text"] = result.get("header")
            args["card_title"] = result.get("card_title")
            args["text_module_rows"] = result.get("text_module_rows", [])
        elif class_type == "EventTicket":
            args["event_name"] = result.get("event_name")
            args["venue_name"] = result.get("venue_name")
            args["venue_address"] = result.get("venue_address")
            args["event_start"] = result.get("event_start")
        elif class_type == "LoyaltyCard":
            args["program_name"] = result.get("program_name")
        elif class_type == "TransitPass":
            args["transit_type"] = result.get("transit_type")

        args_clean = {k: v for k, v in args.items() if v is not None}
        return get_template(class_type, class_id, **args_clean)

    def _class_row_to_dict(self, cls: ClassesTable) -> dict:
        """Convert a ClassesTable ORM instance (with eager children) to a flat dict."""
        d: Dict[str, Any] = {
            "class_id": cls.class_id,
            "class_type": cls.class_type,
            "issuer_name": cls.issuer_name,
            "base_color": cls.base_color,
            "logo_url": cls.logo_url,
            "hero_image_url": cls.hero_image_url,
            "created_at": cls.created_at,
            "updated_at": cls.updated_at,
        }
        # Flatten child fields
        if cls.generic_fields:
            d["header"] = cls.generic_fields.header
            d["card_title"] = cls.generic_fields.card_title
            d["card_title"] = cls.generic_fields.card_title
            d["text_module_rows"] = [
                {
                    "row_index": r.row_index,
                    "left_header": r.left_header, "left_body": r.left_body,
                    "middle_header": r.middle_header, "middle_body": r.middle_body,
                    "right_header": r.right_header, "right_body": r.right_body,
                }
                for r in cls.generic_fields.text_module_rows
            ]
        else:
            d["header"] = None
            d["card_title"] = None
            d["card_title"] = None
            d["text_module_rows"] = []

        if cls.event_ticket_fields:
            d["event_name"] = cls.event_ticket_fields.event_name
            d["venue_name"] = cls.event_ticket_fields.venue_name
            d["venue_address"] = cls.event_ticket_fields.venue_address
            d["event_start"] = cls.event_ticket_fields.event_start
        else:
            d["event_name"] = None
            d["venue_name"] = None
            d["venue_address"] = None
            d["event_start"] = None

        if cls.loyalty_fields:
            d["program_name"] = cls.loyalty_fields.program_name
        else:
            d["program_name"] = None

        if cls.transit_fields:
            d["transit_type"] = cls.transit_fields.transit_type
            d["transit_operator_name"] = cls.transit_fields.transit_operator_name
        else:
            d["transit_type"] = None
            d["transit_operator_name"] = None

        d["class_json"] = self._build_class_json(d)
        return d

    def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        with self.get_session() as session:
            cls = session.get(ClassesTable, class_id)
            if not cls:
                return None
            return self._class_row_to_dict(cls)

    def get_all_classes(self) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = (
                session.query(ClassesTable)
                .order_by(ClassesTable.created_at.desc())
                .all()
            )
            return [self._class_row_to_dict(r) for r in rows]

    def update_class(self, class_id: str, **kwargs) -> bool:
        """Update class across parent + child tables."""
        with self.get_session() as session:
            cls = session.get(ClassesTable, class_id)
            if not cls:
                return False

            # 1. Update parent table fields
            for k in ['class_type', 'issuer_name', 'base_color', 'logo_url', 'hero_image_url']:
                if k in kwargs:
                    setattr(cls, k, kwargs[k])

            # 2. Determine class_type for child table routing
            class_type = kwargs.get('class_type') or cls.class_type

            # 3. Update / upsert child table
            if class_type == 'Generic':
                child_vals = {
                    'header': kwargs.get('header_text'),
                    'card_title': kwargs.get('card_title'),
                }
                child_vals = {k: v for k, v in child_vals.items() if v is not None}
                if child_vals:
                    if cls.generic_fields:
                        for k, v in child_vals.items():
                            setattr(cls.generic_fields, k, v)
                    else:
                        cls.generic_fields = GenericClassFields(
                            class_id=class_id, **child_vals,
                        )
                
                if 'text_module_rows' in kwargs:
                    # Replace all existing module rows
                    if cls.generic_fields:
                        cls.generic_fields.text_module_rows.clear()
                        session.flush()
                        
                    for row in kwargs.get('text_module_rows', []):
                        if hasattr(row, 'dict'):
                            row = row.dict()
                        
                        r_obj = GenericClassTextModuleRows(
                            class_id=class_id,
                            row_index=row.get('row_index', 0),
                            left_header=row.get('left_header'), left_body=row.get('left_body'),
                            middle_header=row.get('middle_header'), middle_body=row.get('middle_body'),
                            right_header=row.get('right_header'), right_body=row.get('right_body')
                        )
                        if cls.generic_fields:
                            cls.generic_fields.text_module_rows.append(r_obj)
                        else:
                            # edge case
                            session.add(r_obj)

            elif class_type == 'EventTicket':
                child_vals = {
                    'event_name': kwargs.get('event_name'),
                    'venue_name': kwargs.get('venue_name'),
                    'venue_address': kwargs.get('venue_address'),
                    'event_start': kwargs.get('event_start'),
                }
                child_vals = {k: v for k, v in child_vals.items() if v is not None}
                if child_vals:
                    if cls.event_ticket_fields:
                        for k, v in child_vals.items():
                            setattr(cls.event_ticket_fields, k, v)
                    else:
                        cls.event_ticket_fields = EventTicketClassFields(
                            class_id=class_id, **child_vals,
                        )

            elif class_type == 'LoyaltyCard':
                pn = kwargs.get('program_name')
                if pn is not None:
                    if cls.loyalty_fields:
                        cls.loyalty_fields.program_name = pn
                    else:
                        cls.loyalty_fields = LoyaltyClassFields(
                            class_id=class_id, program_name=pn,
                        )

            elif class_type == 'TransitPass':
                child_vals = {
                    'transit_type': kwargs.get('transit_type'),
                    'transit_operator_name': kwargs.get('transit_operator_name'),
                }
                child_vals = {k: v for k, v in child_vals.items() if v is not None}
                if child_vals:
                    if cls.transit_fields:
                        for k, v in child_vals.items():
                            setattr(cls.transit_fields, k, v)
                    else:
                        cls.transit_fields = TransitClassFields(
                            class_id=class_id, **child_vals,
                        )

            return True

    def delete_class(self, class_id: str) -> bool:
        """Delete class — CASCADE handles child tables automatically."""
        with self.get_session() as session:
            cls = session.get(ClassesTable, class_id)
            if not cls:
                return False
            session.delete(cls)
            return True

    # ========================================================================
    # Passes_Table Operations (Relational)
    # ========================================================================

    def create_pass(self, object_id: str, class_id: str,
                    holder_name: str, holder_email: str,
                    pass_data: Optional[Dict[str, Any]] = None,
                    status: str = 'Active') -> bool:
        """Create a new pass, splitting pass_data JSON into relational tables"""
        class_info = self.get_class(class_id)
        if not class_info:
            return False

        class_type = class_info.get('class_type', 'Generic')
        pd = pass_data or {}

        with self.get_session() as session:
            # 1. Core pass
            pass_obj = PassesTable(
                object_id=object_id, class_id=class_id,
                holder_name=holder_name, holder_email=holder_email,
                status=status, sync_status='pending',
            )
            session.add(pass_obj)
            session.flush()

            # 2. Type-specific fields
            if class_type == "EventTicket":
                etd = pd.get('event_ticket_data', pd)
                session.add(EventTicketFields(
                    object_id=object_id,
                    ticket_holder_name=etd.get('ticketHolderName', etd.get('ticket_holder_name')),
                    confirmation_code=etd.get('confirmationCode', etd.get('confirmation_code')),
                    seat=etd.get('seatNumber', etd.get('seat')),
                    section=etd.get('section'),
                    gate=etd.get('gate'),
                ))
            else:
                gd = pd.get('generic_data', pd)
                session.add(GenericFields(
                    object_id=object_id,
                    header_value=gd.get('header_value', gd.get('header')),
                    subheader_value=gd.get('subheader_value'),
                    card_title=gd.get('card_title'),
                    logo_url=gd.get('logo_url'),
                    hero_image_url=gd.get('hero_image_url'),
                    hex_background_color=gd.get('hex_background_color', gd.get('hexBackgroundColor')),
                    barcode_type=gd.get('barcode_type', gd.get('barcodeType')),
                    barcode_value=gd.get('barcode_value', gd.get('barcodeValue')),
                ))

            # 3. Text modules
            text_modules = pd.get('textModulesData', pd.get('text_modules', []))
            if isinstance(text_modules, list):
                for idx, mod in enumerate(text_modules):
                    session.add(PassTextModules(
                        object_id=object_id, module_id=mod.get('id'),
                        header=mod.get('header'), body=mod.get('body'),
                        display_order=idx,
                    ))

            # 4. Messages
            messages = pd.get('messages', [])
            if isinstance(messages, list):
                for msg in messages:
                    start_val = msg.get('start_date')
                    end_val = msg.get('end_date')
                    interval = msg.get('displayInterval')
                    if isinstance(interval, dict):
                        start_val = interval.get('start', {}).get('date', start_val)
                        end_val = interval.get('end', {}).get('date', end_val)

                    session.add(PassMessages(
                        object_id=object_id, message_id=msg.get('id'),
                        header=msg.get('header'), body=msg.get('body'),
                        message_type=msg.get('messageType'),
                        start_date=start_val, end_date=end_val,
                    ))

            return True

    def _construct_pass_dictionary(self, p: PassesTable, session: Session) -> dict:
        """Helper to build the combined pass dict from ORM relationships."""
        core: Dict[str, Any] = {
            "object_id": p.object_id,
            "class_id": p.class_id,
            "holder_name": p.holder_name,
            "holder_email": p.holder_email,
            "status": p.status,
            "sync_status": p.sync_status,
            "last_synced_at": p.last_synced_at,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }

        # Determine class type
        parent_cls = p.parent_class
        class_type = parent_cls.class_type if parent_cls else 'Generic'

        # Type-specific fields
        if class_type == "EventTicket" and p.event_ticket_fields:
            et = p.event_ticket_fields
            core['event_ticket_data'] = {
                'ticketHolderName': et.ticket_holder_name,
                'confirmationCode': et.confirmation_code,
                'seatNumber': et.seat,
                'section': et.section,
                'gate': et.gate,
            }
        elif p.generic_fields:
            gf = p.generic_fields
            core['generic_data'] = {
                'header_value': gf.header_value,
                'subheader_value': gf.subheader_value,
                'card_title': gf.card_title,
                'logo_url': gf.logo_url,
                'hero_image_url': gf.hero_image_url,
                'hex_background_color': gf.hex_background_color,
                'hexBackgroundColor': gf.hex_background_color, # Alias for consistency
                'barcode_type': gf.barcode_type,
                'barcode_value': gf.barcode_value,
            }

        # Text modules
        if p.text_modules:
            core['textModulesData'] = [
                {'id': m.module_id, 'header': m.header, 'body': m.body}
                for m in p.text_modules
            ]

        # Messages
        if p.messages:
            core['messages'] = [
                {
                    'id': m.message_id, 'header': m.header, 'body': m.body,
                    'messageType': m.message_type,
                    'start_date': m.start_date, 'end_date': m.end_date,
                }
                for m in p.messages
            ]

        # Legacy pass_data dict for backwards compatibility
        core['pass_data'] = {}
        if 'event_ticket_data' in core:
            core['pass_data'].update(core['event_ticket_data'])
        if 'generic_data' in core:
            core['pass_data'].update(core['generic_data'])
        if 'textModulesData' in core:
            core['pass_data']['textModulesData'] = core['textModulesData']
        if 'messages' in core:
            core['pass_data']['messages'] = core['messages']

        return core

    def get_pass(self, object_id: str) -> Optional[Dict[str, Any]]:
        with self.get_session() as session:
            p = session.get(PassesTable, object_id)
            if not p:
                return None
            return self._construct_pass_dictionary(p, session)

    def get_pass_by_id(self, pass_id: int) -> Optional[Dict[str, Any]]:
        # Deprecated stub
        return None

    def get_passes_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = (
                session.query(PassesTable)
                .filter(PassesTable.class_id == class_id)
                .order_by(PassesTable.created_at.desc())
                .all()
            )
            return [self._construct_pass_dictionary(r, session) for r in rows]

    def get_all_passes(self) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = (
                session.query(PassesTable)
                .order_by(PassesTable.created_at.desc())
                .all()
            )
            return [self._construct_pass_dictionary(r, session) for r in rows]

    def get_active_passes(self) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = (
                session.query(PassesTable)
                .filter(PassesTable.status == 'Active')
                .order_by(PassesTable.created_at.desc())
                .all()
            )
            return [self._construct_pass_dictionary(r, session) for r in rows]

    def get_passes_by_email(self, email: str) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = (
                session.query(PassesTable)
                .filter(PassesTable.holder_email == email)
                .order_by(PassesTable.created_at.desc())
                .all()
            )
            return [self._construct_pass_dictionary(r, session) for r in rows]

    def update_pass(self, object_id: str, **kwargs) -> bool:
        """Update a pass across all relational tables"""
        print(f"DB DEBUG update_pass: object_id={object_id}")
        print(f"DB DEBUG update_pass: kwargs keys = {list(kwargs.keys())}")

        with self.get_session() as session:
            p = session.get(PassesTable, object_id)
            if not p:
                print(f"DB DEBUG: ERROR - pass not found in Passes_Table!")
                return False

            # 1. Core fields
            core_updates = {}
            for k in ['holder_name', 'holder_email', 'status', 'sync_status', 'last_synced_at']:
                if k in kwargs:
                    core_updates[k] = kwargs[k]

            if core_updates:
                print(f"DB DEBUG: Updating core fields: {core_updates}")
                for k, v in core_updates.items():
                    setattr(p, k, v)

            # 2. Handle pass_data (type-specific fields)
            pd = kwargs.get('pass_data')
            if pd and isinstance(pd, dict):
                print(f"DB DEBUG: Processing pass_data: {pd}")

                class_type = p.parent_class.class_type if p.parent_class else "Generic"
                print(f"DB DEBUG: class_type = {class_type}")

                if class_type == "EventTicket":
                    ticket_holder_name = pd.get('ticket_holder_name', pd.get('ticketHolderName'))
                    confirmation_code = pd.get('confirmation_code', pd.get('confirmationCode'))
                    seat = pd.get('seat', pd.get('seatNumber'))
                    section = pd.get('section')
                    gate = pd.get('gate')

                    print(f"DB DEBUG EventTicket: ticket_holder_name={ticket_holder_name}, "
                          f"confirmation_code={confirmation_code}, seat={seat}, "
                          f"section={section}, gate={gate}")

                    if p.event_ticket_fields:
                        et = p.event_ticket_fields
                        et.ticket_holder_name = ticket_holder_name
                        et.confirmation_code = confirmation_code
                        et.seat = seat
                        et.section = section
                        et.gate = gate
                    else:
                        p.event_ticket_fields = EventTicketFields(
                            object_id=object_id,
                            ticket_holder_name=ticket_holder_name,
                            confirmation_code=confirmation_code,
                            seat=seat, section=section, gate=gate,
                        )
                else:
                    header_value = pd.get('header_value', pd.get('header'))
                    subheader_value = pd.get('subheader_value')
                    card_title = pd.get('card_title')
                    logo_url = pd.get('logo_url')
                    hero_image_url = pd.get('hero_image_url')
                    hex_bg = pd.get('hex_background_color', pd.get('hexBackgroundColor'))
                    barcode_type = pd.get('barcode_type', pd.get('barcodeType'))
                    barcode_value = pd.get('barcode_value', pd.get('barcodeValue'))

                    print(f"DB DEBUG Generic: header_value={header_value}, "
                          f"subheader_value={subheader_value}, card_title={card_title}, logo_url={logo_url}")

                    if p.generic_fields:
                        gf = p.generic_fields
                        gf.header_value = header_value
                        gf.subheader_value = subheader_value
                        if card_title is not None:
                            gf.card_title = card_title
                        if logo_url is not None:
                            gf.logo_url = logo_url
                        if hero_image_url is not None:
                            gf.hero_image_url = hero_image_url
                        if hex_bg is not None:
                            gf.hex_background_color = hex_bg
                        if barcode_type is not None:
                            gf.barcode_type = barcode_type
                        if barcode_value is not None:
                            gf.barcode_value = barcode_value
                    else:
                        p.generic_fields = GenericFields(
                            object_id=object_id,
                            header_value=header_value,
                            subheader_value=subheader_value,
                            card_title=card_title,
                            logo_url=logo_url,
                            hero_image_url=hero_image_url,
                            hex_background_color=hex_bg,
                            barcode_type=barcode_type,
                            barcode_value=barcode_value,
                        )

                # Text modules (replace-all strategy)
                if 'textModulesData' in pd or 'text_modules' in pd:
                    p.text_modules.clear()
                    session.flush()
                    text_modules = pd.get('textModulesData', pd.get('text_modules', []))
                    if isinstance(text_modules, list):
                        for idx, mod in enumerate(text_modules):
                            p.text_modules.append(PassTextModules(
                                object_id=object_id, module_id=mod.get('id'),
                                header=mod.get('header'), body=mod.get('body'),
                                display_order=idx,
                            ))

                # Messages (replace-all strategy)
                if 'messages' in pd:
                    p.messages.clear()
                    session.flush()
                    messages = pd.get('messages', [])
                    if isinstance(messages, list):
                        for msg in messages:
                            start_val = msg.get('start_date')
                            end_val = msg.get('end_date')
                            interval = msg.get('displayInterval')
                            if isinstance(interval, dict):
                                start_val = interval.get('start', {}).get('date', start_val)
                                end_val = interval.get('end', {}).get('date', end_val)

                            p.messages.append(PassMessages(
                                object_id=object_id, message_id=msg.get('id'),
                                header=msg.get('header'), body=msg.get('body'),
                                message_type=msg.get('messageType'),
                                start_date=start_val, end_date=end_val,
                            ))

            print(f"DB DEBUG: update_pass complete for {object_id}")
            return True

    def update_pass_status(self, object_id: str, status: str) -> bool:
        if status not in ['Active', 'Expired']:
            raise ValidationError("Status must be 'Active' or 'Expired'")
        return self.update_pass(object_id, status=status)

    def delete_pass(self, object_id: str) -> bool:
        """Delete pass — CASCADE handles child tables automatically."""
        with self.get_session() as session:
            p = session.get(PassesTable, object_id)
            if not p:
                return False
            session.delete(p)
            return True

    # ========================================================================
    # Notifications_Table Operations
    # ========================================================================

    def create_notification(self, class_id: str, object_id: str,
                            status: str, message: str) -> bool:
        with self.get_session() as session:
            session.add(NotificationsTable(
                class_id=class_id, object_id=object_id,
                status=status, message=message,
            ))
            return True

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_pass_with_class(self, object_id: str) -> Optional[Dict[str, Any]]:
        with self.get_session() as session:
            p = session.get(PassesTable, object_id)
            if not p:
                return None
            result = self._construct_pass_dictionary(p, session)
            if p.parent_class:
                result['class_type'] = p.parent_class.class_type
                result['class_json'] = None  # legacy column no longer exists
            return result

    def test_connection(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute(
                    __import__('sqlalchemy').text("SELECT 1")
                )
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    # ========================================================================
    # Apple Wallet Operations
    # ========================================================================
    # Apple Wallet Operations
    # ========================================================================

    def create_apple_pass(self, serial_number: str, template_id: str, holder_name: str, holder_email: str, auth_token: str, status: str = "Active", visual_data: dict = None, fields_data: list = None) -> bool:
        from sqlalchemy.exc import SQLAlchemyError
        import traceback
        
        print(f"🍏 [DEBUG] Attempting to save Apple Pass to DB. Serial: {serial_number}")

        try:
            with self.get_session() as session:
                # 1. Core pass instance
                p = ApplePassesData(
                    pass_id=serial_number,
                    template_id=template_id,
                    holder_name=holder_name,
                    holder_email=holder_email,
                    auth_token=auth_token,
                    status=status,
                    background_color=visual_data.get("background_color") if visual_data else None,
                    foreground_color=visual_data.get("foreground_color") if visual_data else None,
                    label_color=visual_data.get("label_color") if visual_data else None,
                    organization_name=visual_data.get("organization_name") if visual_data else None,
                    logo_text=visual_data.get("logo_text") if visual_data else None,
                    logo_url=visual_data.get("logo_url") if visual_data else None,
                    icon_url=visual_data.get("icon_url") if visual_data else None,
                    strip_url=visual_data.get("strip_url") if visual_data else None,
                )
                session.add(p)
                session.flush() 

                # 2. Dynamic fields (ApplePassFields)
                if fields_data:
                    for f in fields_data:
                        field_obj = ApplePassFields(
                            pass_id=serial_number,
                            field_type=f.get("type"), # 'header', 'primary', etc.
                            field_key=f.get("key"),
                            label=f.get("label"),
                            value=str(f.get("value", ""))
                        )
                        session.add(field_obj)
                
                return True

        except SQLAlchemyError as e:
            print(f"❌ [DB_ERROR] SQLAlchemy failed to save Apple Pass: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"❌ [CRITICAL_ERROR] Unexpected error in create_apple_pass: {e}")
            traceback.print_exc()
            return False

    def _apple_pass_to_dict(self, p: ApplePassesData) -> dict:
        result = {
            "serial_number": p.pass_id,
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
            "admin_message": p.admin_message,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        
        # Add relational fields (anatomical fields)
        if p.fields:
            result["fields"] = [
                {
                    "type": f.field_type,
                    "key": f.field_key,
                    "label": f.label,
                    "value": f.value
                }
                for f in p.fields
            ]
        else:
            result["fields"] = []
            
        return result

    def get_apple_pass(self, serial_number: str) -> Optional[dict]:
        with self.get_session() as session:
            p = session.get(ApplePassesData, serial_number)
            if not p:
                return None
            return self._apple_pass_to_dict(p)

    def get_all_apple_passes(self) -> List[dict]:
        with self.get_session() as session:
            rows = session.query(ApplePassesData).order_by(ApplePassesData.created_at.desc()).all()
            return [self._apple_pass_to_dict(r) for r in rows]

    def update_apple_pass(self, serial_number: str, **kwargs) -> bool:
        with self.get_session() as session:
            p = session.get(ApplePassesData, serial_number)
            if not p:
                return False
                
            for k, v in kwargs.items():
                if hasattr(p, k):
                    setattr(p, k, v)
                    
            return True

    def delete_apple_pass(self, serial_number: str) -> bool:
        with self.get_session() as session:
            p = session.get(ApplePassesData, serial_number)
            if not p:
                return False
            session.delete(p)
            return True

    def update_apple_pass_message(self, serial_number: str, message: str) -> bool:
        """Update the admin_message for a specific Apple pass to trigger lock-screen notification."""
        with self.get_session() as session:
            p = session.get(ApplePassesData, serial_number)
            if not p:
                return False
            p.admin_message = message
            return True

    # ========================================================================
    # Apple Device Registration Operations
    # ========================================================================

    def register_apple_device(self, device_library_id: str, push_token: str, pass_type_id: str, serial_number: str) -> bool:
        with self.get_session() as session:
            # Check if exists
            existing = session.query(AppleDeviceRegistrations).filter_by(
                device_library_id=device_library_id,
                serial_number=serial_number
            ).first()
            
            if existing:
                # Update token if changed
                if existing.push_token != push_token:
                    existing.push_token = push_token
            else:
                reg = AppleDeviceRegistrations(
                    device_library_id=device_library_id,
                    push_token=push_token,
                    pass_type_id=pass_type_id,
                    serial_number=serial_number
                )
                session.add(reg)
            return True

    def unregister_apple_device(self, device_library_id: str, serial_number: str) -> bool:
        with self.get_session() as session:
            existing = session.query(AppleDeviceRegistrations).filter_by(
                device_library_id=device_library_id,
                serial_number=serial_number
            ).first()
            if existing:
                session.delete(existing)
                return True
            return False

    def unregister_apple_device_by_token(self, push_token: str) -> bool:
        """Removes all registrations associated with a specific push token.
        Called when APNs returns a 410 (Unregistered)."""
        with self.get_session() as session:
            session.query(AppleDeviceRegistrations).filter_by(push_token=push_token).delete()
            return True

    def get_registered_devices_for_pass(self, serial_number: str) -> List[str]:
        """Returns list of push tokens for a given pass serial number."""
        with self.get_session() as session:
            rows = session.query(AppleDeviceRegistrations.push_token).filter_by(serial_number=serial_number).all()
            return [r[0] for r in rows]

    def get_passes_by_device(self, device_library_id: str, pass_type_id: str) -> List[str]:
        with self.get_session() as session:
            rows = (
                session.query(ApplePassesData.pass_id)
                .join(AppleDeviceRegistrations, ApplePassesData.pass_id == AppleDeviceRegistrations.serial_number)
                .filter(AppleDeviceRegistrations.device_library_id == device_library_id)
                .filter(AppleDeviceRegistrations.pass_type_id == pass_type_id)
                .all()
            )
            return [r[0] for r in rows]

    def get_apple_passes_updated_since(self, pass_type_id: str, device_library_id: str, passes_updated_since: datetime) -> List[str]:
        with self.get_session() as session:
            rows = (
                session.query(ApplePassesData.pass_id)
                .join(AppleDeviceRegistrations, ApplePassesData.pass_id == AppleDeviceRegistrations.serial_number)
                .filter(AppleDeviceRegistrations.device_library_id == device_library_id)
                .filter(AppleDeviceRegistrations.pass_type_id == pass_type_id)
                .filter(ApplePassesData.updated_at >= passes_updated_since)
                .all()
            )
            return [r[0] for r in rows]

    # ========================================================================
    # Apple Template Operations
    # ========================================================================

    def create_apple_template(self, template_id: str, template_name: str, pass_style: str, pass_type_identifier: str, team_identifier: str) -> bool:
        with self.get_session() as session:
            template = ApplePassesTemplate(
                template_id=template_id,
                template_name=template_name,
                pass_style=pass_style,
                pass_type_identifier=pass_type_identifier,
                team_identifier=team_identifier
            )
            session.add(template)
            return True

    def get_apple_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        with self.get_session() as session:
            t = session.get(ApplePassesTemplate, template_id)
            if not t:
                return None
            return {
                "template_id": t.template_id,
                "template_name": t.template_name,
                "pass_style": t.pass_style,
                "pass_type_identifier": t.pass_type_identifier,
                "team_identifier": t.team_identifier,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }

    def get_all_apple_templates(self) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            rows = session.query(ApplePassesTemplate).order_by(ApplePassesTemplate.created_at.desc()).all()
            return [
                {
                    "template_id": t.template_id,
                    "template_name": t.template_name,
                    "pass_style": t.pass_style,
                    "pass_type_identifier": t.pass_type_identifier,
                    "team_identifier": t.team_identifier,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                }
                for t in rows
            ]

    def update_apple_template(self, template_id: str, **kwargs) -> bool:
        with self.get_session() as session:
            t = session.get(ApplePassesTemplate, template_id)
            if not t:
                return False
            for k, v in kwargs.items():
                if hasattr(t, k):
                    setattr(t, k, v)
            return True

    def delete_apple_template(self, template_id: str) -> bool:
        with self.get_session() as session:
            t = session.get(ApplePassesTemplate, template_id)
            if not t:
                return False
            session.delete(t)
            return True
