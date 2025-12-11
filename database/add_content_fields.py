"""
Database Migration Script
Adds header_text and card_title fields to Classes_Table
"""

import mysql.connector
from mysql.connector import Error
import sys
from pathlib import Path

# Add parent directory to path to import configs
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs


def add_content_fields():
    """Add header_text and card_title columns to Classes_Table"""
    try:
        conn = mysql.connector.connect(
            host=configs.DB_HOST,
            port=configs.DB_PORT,
            user=configs.DB_USER,
            password=configs.DB_PASSWORD,
            database=configs.DB_NAME
        )
        cursor = conn.cursor()
        
        # Check if header_text column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'Classes_Table' 
            AND COLUMN_NAME = 'header_text'
        """, (configs.DB_NAME,))
        
        header_exists = cursor.fetchone()[0]
        
        if not header_exists:
            cursor.execute("""
                ALTER TABLE Classes_Table 
                ADD COLUMN header_text VARCHAR(255) 
                COMMENT 'Header text for the pass'
                AFTER issuer_name
            """)
            print("✓ Column 'header_text' added successfully")
        else:
            print("✓ Column 'header_text' already exists")
        
        # Check if card_title column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'Classes_Table' 
            AND COLUMN_NAME = 'card_title'
        """, (configs.DB_NAME,))
        
        title_exists = cursor.fetchone()[0]
        
        if not title_exists:
            cursor.execute("""
                ALTER TABLE Classes_Table 
                ADD COLUMN card_title VARCHAR(255) 
                COMMENT 'Card title for the pass'
                AFTER header_text
            """)
            print("✓ Column 'card_title' added successfully")
        else:
            print("✓ Column 'card_title' already exists")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"✗ Error adding columns: {e}")
        return False


def main():
    """Main migration function"""
    print("=" * 80)
    print("Database Migration: Add header_text and card_title to Classes_Table")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Host: {configs.DB_HOST}")
    print(f"  Port: {configs.DB_PORT}")
    print(f"  Database: {configs.DB_NAME}")
    print()
    
    print("Running migration...")
    if add_content_fields():
        print()
        print("=" * 80)
        print("✓ Migration completed successfully!")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("✗ Migration failed!")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
