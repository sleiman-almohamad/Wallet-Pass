"""
Fixed Database Initialization Script
Properly creates tables by executing SQL statements one at a time
"""

import mysql.connector
from mysql.connector import Error
import sys
import os
from pathlib import Path

# Add parent directory to path to import configs
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs


def create_tables():
    """Create database tables directly"""
    try:
        conn = mysql.connector.connect(
            host=configs.DB_HOST,
            port=configs.DB_PORT,
            user=configs.DB_USER,
            password=configs.DB_PASSWORD,
            database=configs.DB_NAME
        )
        cursor = conn.cursor()
        
        # Create Classes_Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Classes_Table (
                class_id VARCHAR(255) PRIMARY KEY COMMENT 'Unique identifier for the pass class',
                class_type VARCHAR(100) NOT NULL COMMENT 'Type of pass (e.g., EventTicket, LoyaltyCard)',
                base_color VARCHAR(7) COMMENT 'Hex color code for the pass (e.g., #FF5733)',
                logo_url VARCHAR(500) COMMENT 'URL to the class logo image',
                issuer_name VARCHAR(255) COMMENT 'Name of the issuer/business',
                header_text VARCHAR(255) COMMENT 'Header text for the pass',
                card_title VARCHAR(255) COMMENT 'Card title for the pass',
                class_json JSON COMMENT 'Complete Google Wallet class JSON configuration',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
                
                INDEX idx_class_type (class_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores Google Wallet pass class definitions'
        """)
        print("✓ Classes_Table created")
        
        # Create Passes_Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Passes_Table (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-incrementing primary key',
                object_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'Unique identifier for the pass object',
                class_id VARCHAR(255) NOT NULL COMMENT 'Reference to the pass class',
                holder_name VARCHAR(255) NOT NULL COMMENT 'Name of the pass holder',
                holder_email VARCHAR(255) NOT NULL COMMENT 'Email of the pass holder',
                status ENUM('Active', 'Expired') DEFAULT 'Active' NOT NULL COMMENT 'Current status of the pass',
                pass_data JSON COMMENT 'Flexible JSON data (seat, gate, match_time, etc.)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
                
                CONSTRAINT fk_passes_class_id 
                    FOREIGN KEY (class_id) 
                    REFERENCES Classes_Table(class_id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                
                INDEX idx_class_id (class_id),
                INDEX idx_status (status),
                INDEX idx_holder_email (holder_email),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores individual pass instances'
        """)
        print("✓ Passes_Table created")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"✗ Error creating tables: {e}")
        return False


def insert_sample_data():
    """Insert sample data for testing"""
    try:
        conn = mysql.connector.connect(
            host=configs.DB_HOST,
            port=configs.DB_PORT,
            user=configs.DB_USER,
            password=configs.DB_PASSWORD,
            database=configs.DB_NAME
        )
        cursor = conn.cursor()
        
        # Insert sample classes
        sample_classes = [
            ('event_class_001', 'EventTicket', '#FF5733', 'https://example.com/logos/event.png'),
            ('loyalty_class_001', 'LoyaltyCard', '#3498DB', 'https://example.com/logos/loyalty.png')
        ]
        
        for class_data in sample_classes:
            try:
                cursor.execute(
                    """INSERT INTO Classes_Table (class_id, class_type, base_color, logo_url) 
                       VALUES (%s, %s, %s, %s)""",
                    class_data
                )
            except mysql.connector.IntegrityError:
                pass  # Skip if already exists
        
        # Insert sample passes
        sample_passes = [
            ('pass_001', 'event_class_001', 'John Doe', 'john@example.com', 'Active', 
             '{"seat": "A5", "gate": "3", "match_time": "20:00"}'),
            ('pass_002', 'event_class_001', 'Jane Smith', 'jane@example.com', 'Active',
             '{"seat": "B12", "gate": "2", "match_time": "20:00"}'),
            ('pass_003', 'loyalty_class_001', 'Bob Johnson', 'bob@example.com', 'Active',
             '{"points": 1500, "tier": "Gold", "member_since": "2024-01-15"}')
        ]
        
        for pass_data in sample_passes:
            try:
                cursor.execute(
                    """INSERT INTO Passes_Table 
                       (object_id, class_id, holder_name, holder_email, status, pass_data) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    pass_data
                )
            except mysql.connector.IntegrityError:
                pass  # Skip if already exists
        
        conn.commit()
        print(f"✓ Sample data inserted: {len(sample_classes)} classes, {len(sample_passes)} passes")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"✗ Error inserting sample data: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 80)
    print("MariaDB Database Initialization for Wallet Passes")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Host: {configs.DB_HOST}")
    print(f"  Port: {configs.DB_PORT}")
    print(f"  User: {configs.DB_USER}")
    print(f"  Database: {configs.DB_NAME}")
    print()
    
    # Create tables
    print("Creating tables...")
    if not create_tables():
        print("\n✗ Table creation failed!")
        sys.exit(1)
    print()
    
    # Ask about sample data
    response = input("Do you want to insert sample data for testing? (y/n): ").lower()
    if response == 'y':
        print("\nInserting sample data...")
        insert_sample_data()
        print()
    
    print("=" * 80)
    print("✓ Database initialization completed successfully!")
    print("=" * 80)
    print()
    print("View tables with:")
    print("  uv run python database/view_tables.py")
    print()


if __name__ == "__main__":
    main()
