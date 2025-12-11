"""
Database Migration Script
Adds issuer_name field to Classes_Table
"""

import mysql.connector
from mysql.connector import Error
import sys
from pathlib import Path

# Add parent directory to path to import configs
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs


def add_issuer_name_column():
    """Add issuer_name column to Classes_Table"""
    try:
        conn = mysql.connector.connect(
            host=configs.DB_HOST,
            port=configs.DB_PORT,
            user=configs.DB_USER,
            password=configs.DB_PASSWORD,
            database=configs.DB_NAME
        )
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'Classes_Table' 
            AND COLUMN_NAME = 'issuer_name'
        """, (configs.DB_NAME,))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ Column 'issuer_name' already exists")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE Classes_Table 
                ADD COLUMN issuer_name VARCHAR(255) 
                COMMENT 'Name of the issuer/business'
                AFTER logo_url
            """)
            conn.commit()
            print("✓ Column 'issuer_name' added successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"✗ Error adding column: {e}")
        return False


def main():
    """Main migration function"""
    print("=" * 80)
    print("Database Migration: Add issuer_name to Classes_Table")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Host: {configs.DB_HOST}")
    print(f"  Port: {configs.DB_PORT}")
    print(f"  Database: {configs.DB_NAME}")
    print()
    
    print("Running migration...")
    if add_issuer_name_column():
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
