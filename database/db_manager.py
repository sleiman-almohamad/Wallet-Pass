"""
Database Manager for Wallet Passes
Provides CRUD operations for Classes_Table and Passes_Table
"""

import mysql.connector
from mysql.connector import Error
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import configs


class DatabaseManager:
    """Manages database connections and operations for wallet passes"""
    
    def __init__(self):
        """Initialize database manager with configuration from configs.py"""
        self.config = {
            'host': configs.DB_HOST,
            'port': configs.DB_PORT,
            'user': configs.DB_USER,
            'password': configs.DB_PASSWORD,
            'database': configs.DB_NAME
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            yield conn
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
    
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
                    # Legacy compat (ignored for storage)
                    class_json: Optional[Dict[str, Any]] = None,
                    **extra) -> bool:
        """Create a new pass class in parent + child tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            # 1. Insert parent row
            cursor.execute(
                """INSERT INTO Classes_Table 
                   (class_id, class_type, issuer_name, base_color, logo_url, hero_image_url) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (class_id, class_type, issuer_name, base_color, logo_url, hero_image_url)
            )
            # 2. Insert child row based on type
            if class_type == 'Generic':
                cursor.execute(
                    "INSERT INTO GenericClass_Fields (class_id, header, card_title) VALUES (%s, %s, %s)",
                    (class_id, header_text, card_title)
                )
            elif class_type == 'EventTicket':
                cursor.execute(
                    """INSERT INTO EventTicketClass_Fields 
                       (class_id, event_name, venue_name, venue_address, event_start) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (class_id, event_name, venue_name, venue_address, event_start)
                )
            elif class_type == 'LoyaltyCard':
                cursor.execute(
                    "INSERT INTO LoyaltyClass_Fields (class_id, program_name) VALUES (%s, %s)",
                    (class_id, program_name)
                )
            elif class_type == 'TransitPass':
                cursor.execute(
                    "INSERT INTO TransitClass_Fields (class_id, transit_type, transit_operator_name) VALUES (%s, %s, %s)",
                    (class_id, transit_type, transit_operator_name)
                )
            # GiftCard has no child table
            return cursor.rowcount > 0
    
    def _build_class_json(self, result: dict) -> dict:
        """Helper: synthesize class_json from relational columns using json_templates."""
        from json_templates import get_template
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
    
    def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """SELECT c.*,
                          g.header, g.card_title,
                          e.event_name, e.venue_name, e.venue_address, e.event_start,
                          l.program_name,
                          t.transit_type, t.transit_operator_name
                   FROM Classes_Table c
                   LEFT JOIN GenericClass_Fields g ON c.class_id = g.class_id
                   LEFT JOIN EventTicketClass_Fields e ON c.class_id = e.class_id
                   LEFT JOIN LoyaltyClass_Fields l ON c.class_id = l.class_id
                   LEFT JOIN TransitClass_Fields t ON c.class_id = t.class_id
                   WHERE c.class_id = %s""",
                (class_id,)
            )
            result = cursor.fetchone()
            if result:
                result['class_json'] = self._build_class_json(result)
            return result
    
    def get_all_classes(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """SELECT c.*,
                          g.header, g.card_title,
                          e.event_name, e.venue_name, e.venue_address, e.event_start,
                          l.program_name,
                          t.transit_type, t.transit_operator_name
                   FROM Classes_Table c
                   LEFT JOIN GenericClass_Fields g ON c.class_id = g.class_id
                   LEFT JOIN EventTicketClass_Fields e ON c.class_id = e.class_id
                   LEFT JOIN LoyaltyClass_Fields l ON c.class_id = l.class_id
                   LEFT JOIN TransitClass_Fields t ON c.class_id = t.class_id
                   ORDER BY c.created_at DESC"""
            )
            results = cursor.fetchall()
            for result in results:
                result['class_json'] = self._build_class_json(result)
            return results
    
    def update_class(self, class_id: str, **kwargs) -> bool:
        """Update class across parent + child tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            
            # 1. Update parent table fields
            parent_fields = ['class_type', 'issuer_name', 'base_color', 'logo_url', 'hero_image_url']
            parent_updates = {k: v for k, v in kwargs.items() if k in parent_fields}
            
            if parent_updates:
                set_clause = ", ".join([f"{k} = %s" for k in parent_updates.keys()])
                values = list(parent_updates.values()) + [class_id]
                cursor.execute(f"UPDATE Classes_Table SET {set_clause} WHERE class_id = %s", values)
            
            # 2. Determine class_type for child table routing
            class_type = kwargs.get('class_type')
            if not class_type:
                cursor.execute("SELECT class_type FROM Classes_Table WHERE class_id = %s", (class_id,))
                row = cursor.fetchone()
                class_type = row[0] if row else 'Generic'
            
            # 3. Update child table
            if class_type == 'Generic':
                child_fields = {'header': kwargs.get('header_text'), 'card_title': kwargs.get('card_title')}
                child_fields = {k: v for k, v in child_fields.items() if v is not None}
                if child_fields:
                    cursor.execute("SELECT class_id FROM GenericClass_Fields WHERE class_id = %s", (class_id,))
                    if cursor.fetchone():
                        s = ", ".join([f"{k} = %s" for k in child_fields])
                        cursor.execute(f"UPDATE GenericClass_Fields SET {s} WHERE class_id = %s", list(child_fields.values()) + [class_id])
                    else:
                        cursor.execute("INSERT INTO GenericClass_Fields (class_id, header, card_title) VALUES (%s, %s, %s)",
                                       (class_id, child_fields.get('header'), child_fields.get('card_title')))
                        
            elif class_type == 'EventTicket':
                child_fields = {
                    'event_name': kwargs.get('event_name'), 'venue_name': kwargs.get('venue_name'),
                    'venue_address': kwargs.get('venue_address'), 'event_start': kwargs.get('event_start')
                }
                child_fields = {k: v for k, v in child_fields.items() if v is not None}
                if child_fields:
                    cursor.execute("SELECT class_id FROM EventTicketClass_Fields WHERE class_id = %s", (class_id,))
                    if cursor.fetchone():
                        s = ", ".join([f"{k} = %s" for k in child_fields])
                        cursor.execute(f"UPDATE EventTicketClass_Fields SET {s} WHERE class_id = %s", list(child_fields.values()) + [class_id])
                    else:
                        cursor.execute("INSERT INTO EventTicketClass_Fields (class_id, event_name, venue_name, venue_address, event_start) VALUES (%s, %s, %s, %s, %s)",
                                       (class_id, child_fields.get('event_name'), child_fields.get('venue_name'), child_fields.get('venue_address'), child_fields.get('event_start')))
                        
            elif class_type == 'LoyaltyCard':
                pn = kwargs.get('program_name')
                if pn is not None:
                    cursor.execute("SELECT class_id FROM LoyaltyClass_Fields WHERE class_id = %s", (class_id,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE LoyaltyClass_Fields SET program_name = %s WHERE class_id = %s", (pn, class_id))
                    else:
                        cursor.execute("INSERT INTO LoyaltyClass_Fields (class_id, program_name) VALUES (%s, %s)", (class_id, pn))
                        
            elif class_type == 'TransitPass':
                child_fields = {'transit_type': kwargs.get('transit_type'), 'transit_operator_name': kwargs.get('transit_operator_name')}
                child_fields = {k: v for k, v in child_fields.items() if v is not None}
                if child_fields:
                    cursor.execute("SELECT class_id FROM TransitClass_Fields WHERE class_id = %s", (class_id,))
                    if cursor.fetchone():
                        s = ", ".join([f"{k} = %s" for k in child_fields])
                        cursor.execute(f"UPDATE TransitClass_Fields SET {s} WHERE class_id = %s", list(child_fields.values()) + [class_id])
                    else:
                        cursor.execute("INSERT INTO TransitClass_Fields (class_id, transit_type, transit_operator_name) VALUES (%s, %s, %s)",
                                       (class_id, child_fields.get('transit_type'), child_fields.get('transit_operator_name')))

            return True
    
    def delete_class(self, class_id: str) -> bool:
        """Delete class — CASCADE handles child tables automatically."""
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            cursor.execute("DELETE FROM Classes_Table WHERE class_id = %s", (class_id,))
            return cursor.rowcount > 0
    
    # ========================================================================
    # Passes_Table Operations (Relational)
    # ========================================================================
    
    def create_pass(self, object_id: str, class_id: str, 
                   holder_name: str, holder_email: str,
                   pass_data: Optional[Dict[str, Any]] = None,
                   status: str = 'Active') -> bool:
        """Create a new pass, splitting pass_data JSON into relational tables"""
        # We need the class_type to insert into correct child tables
        class_info = self.get_class(class_id)
        if not class_info:
            return False
            
        class_type = class_info.get('class_type', 'Generic')
        pd = pass_data or {}

        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            
            # 1. Insert Core Pass Info
            cursor.execute(
                """INSERT INTO Passes_Table 
                   (object_id, class_id, holder_name, holder_email, status, sync_status) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (object_id, class_id, holder_name, holder_email, status, 'pending')
            )
            
            # 2. Insert Scalar Type-Specific Info
            if class_type == "EventTicket":
                etd = pd.get('event_ticket_data', pd)
                cursor.execute(
                    """INSERT INTO EventTicket_Fields 
                       (object_id, ticket_holder_name, confirmation_code, seat, section, gate) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (object_id, 
                     etd.get('ticketHolderName', etd.get('ticket_holder_name')),
                     etd.get('confirmationCode', etd.get('confirmation_code')), 
                     etd.get('seatNumber', etd.get('seat')), 
                     etd.get('section'), 
                     etd.get('gate'))
                )
            else:
                gd = pd.get('generic_data', pd)
                cursor.execute(
                    """INSERT INTO Generic_Fields 
                       (object_id, header_value, subheader_value) 
                       VALUES (%s, %s, %s)""",
                    (object_id, gd.get('header_value', gd.get('header')), gd.get('subheader_value'))
                )
                
            # 3. Insert Text Modules Array
            text_modules = pd.get('textModulesData', pd.get('text_modules', []))
            if isinstance(text_modules, list):
                for idx, mod in enumerate(text_modules):
                    cursor.execute(
                        """INSERT INTO Pass_Text_Modules 
                           (object_id, module_id, header, body, display_order) 
                           VALUES (%s, %s, %s, %s, %s)""",
                        (object_id, mod.get('id'), mod.get('header'), mod.get('body'), idx)
                    )
                    
            # 4. Insert Messages Array
            messages = pd.get('messages', [])
            if isinstance(messages, list):
                for msg in messages:
                    # check dict displayInterval
                    start_val = msg.get('start_date')
                    end_val = msg.get('end_date')
                    interval = msg.get('displayInterval')
                    if isinstance(interval, dict):
                        start_val = interval.get('start', {}).get('date', start_val)
                        end_val = interval.get('end', {}).get('date', end_val)
                        
                    cursor.execute(
                        """INSERT INTO Pass_Messages 
                           (object_id, message_id, header, body, message_type, start_date, end_date) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (object_id, msg.get('id'), msg.get('header'), msg.get('body'), msg.get('messageType'), start_val, end_val)
                    )
            
            return True
            
    def _construct_pass_dictionary(self, core_result: dict, cursor) -> dict:
        """Helper to fetch array children and construct the combined pass Pydantic struct"""
        object_id = core_result['object_id']
        
        # Determine class type
        cursor.execute("SELECT class_type FROM Classes_Table WHERE class_id = %s", (core_result['class_id'],))
        c_res = cursor.fetchone()
        class_type = c_res['class_type'] if c_res else 'Generic'
        
        # Fetch Type-Specific Fields
        if class_type == "EventTicket":
            cursor.execute("SELECT * FROM EventTicket_Fields WHERE object_id = %s", (object_id,))
            et_fields = cursor.fetchone()
            if et_fields:
                core_result['event_ticket_data'] = {
                    'ticketHolderName': et_fields['ticket_holder_name'],
                    'confirmationCode': et_fields['confirmation_code'],
                    'seatNumber': et_fields['seat'],
                    'section': et_fields['section'],
                    'gate': et_fields['gate']
                }
        else:
            cursor.execute("SELECT * FROM Generic_Fields WHERE object_id = %s", (object_id,))
            g_fields = cursor.fetchone()
            if g_fields:
                core_result['generic_data'] = {
                    'header_value': g_fields['header_value'],
                    'subheader_value': g_fields['subheader_value']
                }
                
        # Fetch Text Modules
        cursor.execute("SELECT * FROM Pass_Text_Modules WHERE object_id = %s ORDER BY display_order ASC", (object_id,))
        text_mods = cursor.fetchall()
        if text_mods:
            core_result['textModulesData'] = [
                {'id': m['module_id'], 'header': m['header'], 'body': m['body']} for m in text_mods
            ]
            
        # Fetch Messages
        cursor.execute("SELECT * FROM Pass_Messages WHERE object_id = %s", (object_id,))
        msgs = cursor.fetchall()
        if msgs:
            core_result['messages'] = [
                {
                    'id': m['message_id'], 
                    'header': m['header'], 
                    'body': m['body'], 
                    'messageType': m['message_type'],
                    'start_date': m['start_date'],
                    'end_date': m['end_date']
                } for m in msgs
            ]
            
        # Emulate legacy pass_data dict for backwards compatibility on UI rendering functions
        core_result['pass_data'] = {}
        if 'event_ticket_data' in core_result: core_result['pass_data'].update(core_result['event_ticket_data'])
        if 'generic_data' in core_result: core_result['pass_data'].update(core_result['generic_data'])
        if 'textModulesData' in core_result: core_result['pass_data']['textModulesData'] = core_result['textModulesData']
        if 'messages' in core_result: core_result['pass_data']['messages'] = core_result['messages']

        return core_result
    
    def get_pass(self, object_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Passes_Table WHERE object_id = %s", (object_id,))
            result = cursor.fetchone()
            if not result:
                return None
            return self._construct_pass_dictionary(result, cursor)
            
    def get_pass_by_id(self, pass_id: int) -> Optional[Dict[str, Any]]:
        # This function should be deprecated since we removed `id` INT AUTO_INCREMENT
        # but leaving a stub in case any stragglers call it (they shouldn't)
        return None
    
    def get_passes_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Passes_Table WHERE class_id = %s ORDER BY created_at DESC", (class_id,))
            results = cursor.fetchall()
            return [self._construct_pass_dictionary(r, cursor) for r in results]
    
    def get_all_passes(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Passes_Table ORDER BY created_at DESC")
            results = cursor.fetchall()
            return [self._construct_pass_dictionary(r, cursor) for r in results]
    
    def get_active_passes(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Passes_Table WHERE status = 'Active' ORDER BY created_at DESC")
            results = cursor.fetchall()
            return [self._construct_pass_dictionary(r, cursor) for r in results]
            
    def get_passes_by_email(self, email: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Passes_Table WHERE holder_email = %s ORDER BY created_at DESC", (email,))
            results = cursor.fetchall()
            return [self._construct_pass_dictionary(r, cursor) for r in results]
    
    def update_pass(self, object_id: str, **kwargs) -> bool:
        """Update a pass across all relational tables"""
        print(f"DB DEBUG update_pass: object_id={object_id}")
        print(f"DB DEBUG update_pass: kwargs keys = {list(kwargs.keys())}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            
            # 1. Update Core Fields in Passes_Table
            core_updates = {}
            for k in ['holder_name', 'holder_email', 'status', 'sync_status', 'last_synced_at']:
                if k in kwargs:
                    core_updates[k] = kwargs[k]
                    
            if core_updates:
                print(f"DB DEBUG: Updating core fields: {core_updates}")
                set_clause = ", ".join([f"{k} = %s" for k in core_updates.keys()])
                values = list(core_updates.values()) + [object_id]
                cursor.execute(f"UPDATE Passes_Table SET {set_clause} WHERE object_id = %s", values)
                print(f"DB DEBUG: Core rows affected: {cursor.rowcount}")
                
            # 2. Handle pass_data (type-specific fields)
            pd = kwargs.get('pass_data')
            if pd and isinstance(pd, dict):
                print(f"DB DEBUG: Processing pass_data: {pd}")
                
                # Determine class type
                cursor.execute("SELECT class_id FROM Passes_Table WHERE object_id = %s", (object_id,))
                c_id_res = cursor.fetchone()
                if not c_id_res:
                    print(f"DB DEBUG: ERROR - pass not found in Passes_Table!")
                    return False
                    
                class_id = c_id_res[0]
                cursor.execute("SELECT class_type FROM Classes_Table WHERE class_id = %s", (class_id,))
                c_type_res = cursor.fetchone()
                class_type = c_type_res[0] if c_type_res else "Generic"
                print(f"DB DEBUG: class_type = {class_type}")
                    
                if class_type == "EventTicket":
                    # Map flat UI keys to DB columns
                    ticket_holder_name = pd.get('ticket_holder_name', pd.get('ticketHolderName'))
                    confirmation_code = pd.get('confirmation_code', pd.get('confirmationCode'))
                    seat = pd.get('seat', pd.get('seatNumber'))
                    section = pd.get('section')
                    gate = pd.get('gate')
                    
                    print(f"DB DEBUG EventTicket: ticket_holder_name={ticket_holder_name}, confirmation_code={confirmation_code}, seat={seat}, section={section}, gate={gate}")
                    
                    cursor.execute(
                        """INSERT INTO EventTicket_Fields 
                           (object_id, ticket_holder_name, confirmation_code, seat, section, gate) 
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE 
                           ticket_holder_name=VALUES(ticket_holder_name), 
                           confirmation_code=VALUES(confirmation_code), 
                           seat=VALUES(seat), 
                           section=VALUES(section), 
                           gate=VALUES(gate)""",
                        (object_id, ticket_holder_name, confirmation_code, seat, section, gate)
                    )
                    print(f"DB DEBUG EventTicket: rows affected: {cursor.rowcount}")
                    
                else:
                    # Generic pass type
                    header_value = pd.get('header_value', pd.get('header'))
                    subheader_value = pd.get('subheader_value')
                    
                    print(f"DB DEBUG Generic: header_value={header_value}, subheader_value={subheader_value}")
                    
                    cursor.execute(
                        """INSERT INTO Generic_Fields 
                           (object_id, header_value, subheader_value) 
                           VALUES (%s, %s, %s)
                           ON DUPLICATE KEY UPDATE 
                           header_value=VALUES(header_value), 
                           subheader_value=VALUES(subheader_value)""",
                        (object_id, header_value, subheader_value)
                    )
                    print(f"DB DEBUG Generic: rows affected: {cursor.rowcount}")
                            
                # Update Text Modules Array
                if 'textModulesData' in pd or 'text_modules' in pd:
                    cursor.execute("DELETE FROM Pass_Text_Modules WHERE object_id = %s", (object_id,))
                    text_modules = pd.get('textModulesData', pd.get('text_modules', []))
                    if isinstance(text_modules, list):
                        for idx, mod in enumerate(text_modules):
                            cursor.execute(
                                """INSERT INTO Pass_Text_Modules (object_id, module_id, header, body, display_order) 
                                   VALUES (%s, %s, %s, %s, %s)""",
                                (object_id, mod.get('id'), mod.get('header'), mod.get('body'), idx)
                            )
                                
                # Update Messages Array
                if 'messages' in pd:
                    cursor.execute("DELETE FROM Pass_Messages WHERE object_id = %s", (object_id,))
                    messages = pd.get('messages', [])
                    if isinstance(messages, list):
                        for msg in messages:
                            start_val = msg.get('start_date')
                            end_val = msg.get('end_date')
                            interval = msg.get('displayInterval')
                            if isinstance(interval, dict):
                                start_val = interval.get('start', {}).get('date', start_val)
                                end_val = interval.get('end', {}).get('date', end_val)
                                
                            cursor.execute(
                                """INSERT INTO Pass_Messages (object_id, message_id, header, body, message_type, start_date, end_date) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                (object_id, msg.get('id'), msg.get('header'), msg.get('body'), msg.get('messageType'), start_val, end_val)
                            )

            print(f"DB DEBUG: update_pass complete for {object_id}")
            return True
    
    def update_pass_status(self, object_id: str, status: str) -> bool:
        if status not in ['Active', 'Expired']:
            raise ValueError("Status must be 'Active' or 'Expired'")
        return self.update_pass(object_id, status=status)
    
    def delete_pass(self, object_id: str) -> bool:
        # ON DELETE CASCADE handles child tables automatically
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            cursor.execute("DELETE FROM Passes_Table WHERE object_id = %s", (object_id,))
            return cursor.rowcount > 0
    
    # ========================================================================
    # Notifications_Table Operations
    # ========================================================================

    def create_notification(self, class_id: str, object_id: str, status: str, message: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                """INSERT INTO Notifications_Table 
                   (class_id, object_id, status, message) 
                   VALUES (%s, %s, %s, %s)""",
                (class_id, object_id, status, message)
            )
            return cursor.rowcount > 0

    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_pass_with_class(self, object_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """SELECT p.*, c.class_type, c.class_json
                   FROM Passes_Table p
                   JOIN Classes_Table c ON p.class_id = c.class_id
                   WHERE p.object_id = %s""",
                (object_id,)
            )
            result = cursor.fetchone()
            if not result:
                return None
            return self._construct_pass_dictionary(result, cursor)
            
    def test_connection(self) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
