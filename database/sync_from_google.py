#!/usr/bin/env python3
"""
Sync Google Wallet Classes to Local Database

This script fetches all pass classes from Google Wallet API
and imports them into the local MariaDB database.

Usage:
    uv run python database/sync_from_google.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wallet_service import WalletClient
from api_client import APIClient
from google_wallet_parser import parse_google_wallet_class
import json


def sync_classes_from_google():
    """Fetch all classes from Google Wallet and save to local database"""
    
    print("=" * 80)
    print("Syncing Classes from Google Wallet to Local Database")
    print("=" * 80)
    print()
    
    # Initialize clients
    print("🔌 Connecting to Google Wallet API...")
    try:
        wallet_client = WalletClient()
        print("✅ Connected to Google Wallet")
    except Exception as e:
        print(f"❌ Failed to connect to Google Wallet: {e}")
        return False
    
    print("🔌 Connecting to local database...")
    try:
        api_client = APIClient()
        print("✅ Connected to local database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("   Make sure the API server is running: uvicorn api.api:app --reload")
        return False
    
    print()
    
    # Fetch all classes from Google Wallet
    print("📥 Fetching classes from Google Wallet...")
    try:
        google_classes = wallet_client.list_all_classes()
        print(f"✅ Found {len(google_classes)} classes in Google Wallet")
    except Exception as e:
        print(f"❌ Error fetching classes: {e}")
        return False
    
    if not google_classes:
        print("ℹ️  No classes found in Google Wallet")
        return True
    
    print()
    print("=" * 80)
    print("Importing Classes:")
    print("=" * 80)
    
    # Import each class
    imported = 0
    updated = 0
    errors = 0
    
    for google_class in google_classes:
        class_id_full = google_class.get("id", "")
        # Remove issuer prefix for local database
        class_id = class_id_full.split('.')[-1] if '.' in class_id_full else class_id_full
        class_type = google_class.get("class_type", "Generic")
        
        print(f"\n📦 Processing: {class_id} ({class_type})")
        
        try:
            # Parse all fields from Google Wallet class
            metadata = parse_google_wallet_class(google_class)
            # Use the parser's class_type (more reliable detection)
            class_type = metadata.get('class_type', class_type)
            
            # Build kwargs for API calls (all fields the parser extracted)
            class_kwargs = {
                'class_id': class_id,
                'class_type': class_type,
                'issuer_name': metadata.get('issuer_name'),
                'base_color': metadata.get('base_color'),
                'logo_url': metadata.get('logo_url'),
                'hero_image_url': metadata.get('hero_image_url'),
                'header_text': metadata.get('header_text'),
                'card_title': metadata.get('card_title'),
                'event_name': metadata.get('event_name'),
                'venue_name': metadata.get('venue_name'),
                'venue_address': metadata.get('venue_address'),
                'event_start': metadata.get('event_start'),
                'program_name': metadata.get('program_name'),
                'transit_type': metadata.get('transit_type'),
                'transit_operator_name': metadata.get('transit_operator_name'),
            }
            
            # Check if class already exists in local database
            existing = api_client.get_class(class_id)
            
            if existing:
                print(f"   ⚠️  Class exists, updating...")
                api_client.update_class(**class_kwargs)
                print(f"   ✅ Updated: {class_id}")
                updated += 1
            else:
                print(f"   ➕ Creating new class...")
                api_client.create_class(**class_kwargs)
                print(f"   ✅ Imported: {class_id}")
                imported += 1
                
        except Exception as e:
            print(f"   ❌ Error processing {class_id}: {e}")
            errors += 1
    
    print()
    print("=" * 80)
    print("Sync Complete!")
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   • Imported: {imported} new classes")
    print(f"   • Updated:  {updated} existing classes")
    print(f"   • Errors:   {errors}")
    print(f"   • Total:    {len(google_classes)} classes processed")
    print()
    
    return errors == 0


def main():
    """Main function"""
    success = sync_classes_from_google()
    
    if success:
        print("✅ All classes synced successfully!")
        print()
        print("You can now use these templates in:")
        print("  • Pass Generator")
        print("  • Manage Templates")
        print()
    else:
        print("⚠️  Sync completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
