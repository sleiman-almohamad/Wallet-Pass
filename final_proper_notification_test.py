"""
Google Wallet Notification Test - PROPER APPROACH
==================================================
This script follows Google's best practices:
- Uses fresh pass IDs to avoid spam flags
- Sends minimal, properly formatted messages
- Respects rate limits
- Sets realistic expectations
"""

import sys
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wallet_service import WalletClient
import configs

def test_notification_properly(class_id):
    """
    Test Google Wallet notifications the RIGHT way.
    """
    print("="*70)
    print("🔔 GOOGLE WALLET NOTIFICATION TEST - REALISTIC EXPECTATIONS")
    print("="*70)
    print()
    print("⚠️  IMPORTANT REALITY CHECK:")
    print("   - Google Wallet notifications are LOW PRIORITY")
    print("   - They rarely make sounds or show lockscreen banners")
    print("   - Max 3 notifications per pass per 24 hours")
    print("   - Success = message appears in Google Wallet app")
    print("   - DO NOT expect loud sounds or vibrations")
    print()
    print("="*70)
    
    client = WalletClient()
    
    # Prepare class ID
    if not class_id.startswith(configs.ISSUER_ID):
        full_class_id = f"{configs.ISSUER_ID}.{class_id}"
    else:
        full_class_id = class_id
    
    # Generate a COMPLETELY FRESH object ID
    fresh_object_id = f"{configs.ISSUER_ID}.notification_test_{int(time.time())}"
    
    print(f"📝 Step 1: Create a NEW pass")
    print(f"   Class ID: {full_class_id}")
    print(f"   Object ID: {fresh_object_id}")
    print()
    print("INSTRUCTIONS:")
    print("1. Open your Flet app or use the API")
    print(f"2. Create a pass with Object ID: {fresh_object_id}")
    print("3. Add it to Google Wallet on your phone")
    print("4. WAIT for it to sync")
    print()
    
    input("⏸️  Press Enter AFTER the pass is saved to your phone...")
    
    print()
    print("="*70)
    print("📤 Step 2: Sending notification...")
    print("="*70)
    
    # Wait a bit to avoid immediate spam detection
    print("⏳ Waiting 5 seconds to avoid spam detection...")
    time.sleep(5)
    
    # Create a simple, clean message
    message_id = f"notif_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    
    # Minimal patch - just add a message
    patch_body = {
        "messages": [{
            "header": "Test Notification",
            "body": f"Sent at {datetime.now().strftime('%H:%M:%S')}. If you see this in Google Wallet, it worked!",
            "kind": "walletobjects#walletObjectMessage",
            "id": message_id,
            "messageType": "TEXT",
            "displayInterval": {
                "start": {"date": (now - timedelta(minutes=1)).isoformat() + "Z"},
                "end": {"date": (now + timedelta(days=1)).isoformat() + "Z"}
            }
        }]
    }
    
    try:
        # Attempt to send (adjust resource type as needed)
        # Try eventticketobject first, modify if using a different class type
        client.service.eventticketobject().patch(
            resourceId=fresh_object_id,
            body=patch_body
        ).execute()
        
        print(f"✅ Notification sent successfully!")
        print()
        print("="*70)
        print("📱 WHAT TO DO NOW:")
        print("="*70)
        print()
        print("1. OPEN Google Wallet app on your phone")
        print("2. Find the pass you just created")
        print("3. Look for the message in the pass details")
        print()
        print("Expected result:")
        print("   ✅ Message appears in Google Wallet when you open the pass")
        print()
        print("DO NOT EXPECT:")
        print("   ❌ Lockscreen notification banner")
        print("   ❌ Notification sound or vibration")
        print("   ❌ Badge on the app icon")
        print()
        print("If the message appears in Google Wallet, YOUR CODE IS WORKING.")
        print("The lack of sound/banner is a Google Wallet limitation, not a bug.")
        print()
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        print()
        print("Common errors:")
        print("- 'Resource not found': The pass wasn't created yet")
        print("- 'Invalid resource': Wrong class type in the code")
        print("- 'Permission denied': Credentials issue")


if __name__ == "__main__":
    print()
    class_id = input("Enter your Class ID (e.g., MensaParty): ").strip()
    
    if not class_id:
        print("❌ No class ID provided")
        sys.exit(1)
    
    print()
    test_notification_properly(class_id)
