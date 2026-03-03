"""
Database Migration Script
Adds class_json column to Classes_Table for storing complete Google Wallet class JSON
"""

import mysql.connector
from mysql.connector import Error
import sys
from pathlib import Path

# Add parent directory to path to import configs
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs


def add_class_json_column():
    """Add class_json column to Classes_Table"""
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
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'Classes_Table' 
            AND COLUMN_NAME = 'class_json'
        """, (configs.DB_NAME,))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("✓ Column 'class_json' already exists in Classes_Table")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE Classes_Table 
                ADD COLUMN class_json JSON COMMENT 'Complete Google Wallet class JSON configuration'
            """)
            conn.commit()
            print("✓ Successfully added 'class_json' column to Classes_Table")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"✗ Error adding column: {e}")
        return False


def main():
    """Main migration function"""
    print("=" * 80)
    print("Database Migration: Add class_json Column")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Host: {configs.DB_HOST}")
    print(f"  Port: {configs.DB_PORT}")
    print(f"  Database: {configs.DB_NAME}")
    print()
    
    print("Adding class_json column to Classes_Table...")
    if add_class_json_column():
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
