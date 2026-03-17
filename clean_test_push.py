import sys
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wallet_service import WalletClient
import configs

def run_ultimate_sound_test(class_id):
    print("="*60)
    print("🔔 ULTIMATE SOUND TEST: BYPASSING SILENCE")
    print("="*60)

    client = WalletClient()
    
    # Generate a fresh Object ID to avoid previous "Spam" flags
    fresh_id = f"{configs.ISSUER_ID}.final_test_{int(time.time())}"
    
    print(f"1. Open your Flet app and create a pass with this ID: {fresh_id}")
    input("Press Enter AFTER you have added this NEW pass to your phone...")

    # Building the high-priority message
    message_id = f"urgent_{uuid.uuid4().hex[:6]}"
    
    patch_body = {
        "messages": [{
            "header": "⚡ URGENT: SYSTEM ALERT",
            "body": "This notification MUST make a sound. Testing high-priority channel.",
            "kind": "walletobjects#walletObjectMessage",
            "id": message_id,
            "messageType": "TEXT" # In some classes, "EXPIRATION_NOTIFICATION" is even louder
        }]
    }

    try:
        # Using eventticketobject as an example, ensure it matches your class type
        client.service.eventticketobject().patch(
            resourceId=fresh_id, 
            body=patch_body
        ).execute()
        
        print(f"✅ Message sent to {fresh_id}")
        print("📢 Look at your phone screen NOW (keep it locked).")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_ultimate_sound_test("MensaParty")