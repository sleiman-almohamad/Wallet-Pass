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
            # Parse metadata from Google Wallet class
            metadata = parse_google_wallet_class(google_class)
            
            # Extract visual properties
            base_color = metadata.get("base_color")
            logo_url = metadata.get("logo_url")
            
            # Extract text fields based on class type
            issuer_name = None
            header_text = None
            card_title = None
            
            if class_type == "LoyaltyCard":
                issuer_name = google_class.get("localizedIssuerName", {}).get("defaultValue", {}).get("value")
                card_title = google_class.get("localizedProgramName", {}).get("defaultValue", {}).get("value")
            elif class_type == "EventTicket":
                issuer_name = google_class.get("issuerName")
                card_title = google_class.get("eventName", {}).get("defaultValue", {}).get("value")
            elif class_type == "Generic":
                issuer_name = google_class.get("issuerName")
                header_text = google_class.get("header", {}).get("defaultValue", {}).get("value")
                card_title = google_class.get("cardTitle", {}).get("defaultValue", {}).get("value")
            
            # Check if class already exists in local database
            existing = api_client.get_class(class_id)
            
            if existing:
                # Update existing class
                print(f"   ⚠️  Class exists, updating...")
                api_client.update_class(
                    class_id=class_id,
                    class_type=class_type,
                    base_color=base_color,
                    logo_url=logo_url,
                    issuer_name=issuer_name,
                    header_text=header_text,
                    card_title=card_title,
                    class_json=google_class
                )
                print(f"   ✅ Updated: {class_id}")
                updated += 1
            else:
                # Create new class
                print(f"   ➕ Creating new class...")
                api_client.create_class(
                    class_id=class_id,
                    class_type=class_type,
                    base_color=base_color,
                    logo_url=logo_url,
                    issuer_name=issuer_name,
                    header_text=header_text,
                    card_title=card_title,
                    class_json=google_class
                )
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
