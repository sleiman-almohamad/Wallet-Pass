"""
Database Initialization Script — SQLAlchemy edition
Creates all tables using the ORM model metadata.
"""

import sys
from pathlib import Path

# Add parent directory to path to import configs
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import Base, engine


def create_tables():
    """Create all database tables from SQLAlchemy models"""
    try:
        Base.metadata.create_all(engine)
        print("✓ All tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def main():
    """Main initialization function"""
    import configs

    print("=" * 80)
    print("MariaDB Database Initialization for Wallet Passes (SQLAlchemy)")
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

    print("=" * 80)
    print("✓ Database initialization completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
