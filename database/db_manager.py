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
    # Classes_Table Operations
    # ========================================================================
    
    def create_class(self, class_id: str, class_type: str, 
                    base_color: Optional[str] = None, 
                    logo_url: Optional[str] = None,
                    issuer_name: Optional[str] = None,
                    header_text: Optional[str] = None,
                    card_title: Optional[str] = None,
                    class_json: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new pass class
        
        Args:
            class_id: Unique identifier for the class
            class_type: Type of pass (e.g., 'EventTicket', 'LoyaltyCard')
            base_color: Hex color code (e.g., '#FF5733')
            logo_url: URL to the class logo
            issuer_name: Name of the issuer/business
            header_text: Header text for the pass
            card_title: Card title for the pass
            class_json: Complete Google Wallet class JSON configuration
            
        Returns:
            True if successful, False otherwise
        """
        class_json_str = json.dumps(class_json) if class_json else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO Classes_Table 
                   (class_id, class_type, base_color, logo_url, issuer_name, header_text, card_title, class_json) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (class_id, class_type, base_color, logo_url, issuer_name, header_text, card_title, class_json_str)
            )
            return cursor.rowcount > 0
    
    def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a class by ID
        
        Args:
            class_id: The class identifier
            
        Returns:
            Dictionary with class data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Classes_Table WHERE class_id = %s",
                (class_id,)
            )
            result = cursor.fetchone()
            if result and result.get('class_json'):
                # Parse JSON string to dict if it's a string
                if isinstance(result['class_json'], str):
                    result['class_json'] = json.loads(result['class_json'])
            return result
    
    def get_all_classes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all classes
        
        Returns:
            List of dictionaries with class data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Classes_Table ORDER BY created_at DESC")
            results = cursor.fetchall()
            for result in results:
                if result and result.get('class_json'):
                    # Parse JSON string to dict if it's a string
                    if isinstance(result['class_json'], str):
                        result['class_json'] = json.loads(result['class_json'])
            return results
    
    def update_class(self, class_id: str, **kwargs) -> bool:
        """
        Update a class's fields
        
        Args:
            class_id: The class identifier
            **kwargs: Fields to update (class_type, base_color, logo_url, issuer_name, header_text, card_title, class_json)
            
        Returns:
            True if successful, False otherwise
        """
        allowed_fields = ['class_type', 'base_color', 'logo_url', 'issuer_name', 'header_text', 'card_title', 'class_json']
        updates = {}
        
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == 'class_json' and isinstance(v, dict):
                    updates[k] = json.dumps(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [class_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE Classes_Table SET {set_clause} WHERE class_id = %s",
                values
            )
            return cursor.rowcount > 0
    
    def delete_class(self, class_id: str) -> bool:
        """
        Delete a class (will cascade delete associated passes)
        
        Args:
            class_id: The class identifier
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Classes_Table WHERE class_id = %s", (class_id,))
            return cursor.rowcount > 0
    
    # ========================================================================
    # Passes_Table Operations
    # ========================================================================
    
    def create_pass(self, object_id: str, class_id: str, 
                   holder_name: str, holder_email: str,
                   pass_data: Optional[Dict[str, Any]] = None,
                   status: str = 'Active') -> bool:
        """
        Create a new pass
        
        Args:
            object_id: Unique identifier for the pass object
            class_id: Reference to the class
            holder_name: Name of the pass holder
            holder_email: Email of the pass holder
            pass_data: JSON data (seat, gate, match_time, etc.)
            status: Pass status ('Active' or 'Expired')
            
        Returns:
            True if successful, False otherwise
        """
        pass_data_json = json.dumps(pass_data) if pass_data else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO Passes_Table 
                   (object_id, class_id, holder_name, holder_email, status, pass_data) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (object_id, class_id, holder_name, holder_email, status, pass_data_json)
            )
            return cursor.rowcount > 0
    
    def get_pass(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a pass by object ID
        
        Args:
            object_id: The pass object identifier
            
        Returns:
            Dictionary with pass data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE object_id = %s",
                (object_id,)
            )
            result = cursor.fetchone()
            if result and result.get('pass_data'):
                result['pass_data'] = json.loads(result['pass_data'])
            return result
    
    def get_pass_by_id(self, pass_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a pass by auto-increment ID
        
        Args:
            pass_id: The pass ID
            
        Returns:
            Dictionary with pass data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE id = %s",
                (pass_id,)
            )
            result = cursor.fetchone()
            if result and result.get('pass_data'):
                result['pass_data'] = json.loads(result['pass_data'])
            return result
    
    def get_passes_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """
        Get all passes for a specific class
        
        Args:
            class_id: The class identifier
            
        Returns:
            List of dictionaries with pass data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE class_id = %s ORDER BY created_at DESC",
                (class_id,)
            )
            results = cursor.fetchall()
            for result in results:
                if result.get('pass_data'):
                    result['pass_data'] = json.loads(result['pass_data'])
            return results
    
    def get_passes_by_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all passes for a specific user email
        
        Args:
            email: The holder's email
            
        Returns:
            List of dictionaries with pass data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE holder_email = %s ORDER BY created_at DESC",
                (email,)
            )
            results = cursor.fetchall()
            for result in results:
                if result.get('pass_data'):
                    result['pass_data'] = json.loads(result['pass_data'])
            return results
    
    def get_all_passes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all passes
        
        Returns:
            List of dictionaries with pass data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Passes_Table ORDER BY created_at DESC")
            results = cursor.fetchall()
            for result in results:
                if result.get('pass_data'):
                    result['pass_data'] = json.loads(result['pass_data'])
            return results
    
    def get_active_passes(self) -> List[Dict[str, Any]]:
        """
        Get all active passes
        
        Returns:
            List of dictionaries with active pass data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE status = 'Active' ORDER BY created_at DESC"
            )
            results = cursor.fetchall()
            for result in results:
                if result.get('pass_data'):
                    result['pass_data'] = json.loads(result['pass_data'])
            return results
    
    def get_expired_passes(self) -> List[Dict[str, Any]]:
        """
        Get all expired passes
        
        Returns:
            List of dictionaries with expired pass data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Passes_Table WHERE status = 'Expired' ORDER BY created_at DESC"
            )
            results = cursor.fetchall()
            for result in results:
                if result.get('pass_data'):
                    result['pass_data'] = json.loads(result['pass_data'])
            return results
    
    def update_pass(self, object_id: str, **kwargs) -> bool:
        """
        Update a pass's fields
        
        Args:
            object_id: The pass object identifier
            **kwargs: Fields to update (holder_name, holder_email, status, pass_data)
            
        Returns:
            True if successful, False otherwise
        """
        allowed_fields = ['holder_name', 'holder_email', 'status', 'pass_data']
        updates = {}
        
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == 'pass_data' and isinstance(v, dict):
                    updates[k] = json.dumps(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [object_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE Passes_Table SET {set_clause} WHERE object_id = %s",
                values
            )
            return cursor.rowcount > 0
    
    def update_pass_status(self, object_id: str, status: str) -> bool:
        """
        Update a pass's status
        
        Args:
            object_id: The pass object identifier
            status: New status ('Active' or 'Expired')
            
        Returns:
            True if successful, False otherwise
        """
        if status not in ['Active', 'Expired']:
            raise ValueError("Status must be 'Active' or 'Expired'")
        
        return self.update_pass(object_id, status=status)
    
    def delete_pass(self, object_id: str) -> bool:
        """
        Delete a pass
        
        Args:
            object_id: The pass object identifier
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Passes_Table WHERE object_id = %s", (object_id,))
            return cursor.rowcount > 0
    
    # ========================================================================
    # Notifications_Table Operations
    # ========================================================================

    def create_notification(self, class_id: str, object_id: str, status: str, message: str) -> bool:
        """
        Log a notification attempt
        
        Args:
            class_id: The class ID
            object_id: The pass object ID
            status: Status of the notification ('Sent', 'Failed')
            message: Details or error message
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
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
        """
        Get pass data along with its class information
        
        Args:
            object_id: The pass object identifier
            
        Returns:
            Dictionary with combined pass and class data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT p.*, c.class_type, c.base_color, c.logo_url
                   FROM Passes_Table p
                   JOIN Classes_Table c ON p.class_id = c.class_id
                   WHERE p.object_id = %s""",
                (object_id,)
            )
            result = cursor.fetchone()
            if result and result.get('pass_data'):
                result['pass_data'] = json.loads(result['pass_data'])
            return result
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
