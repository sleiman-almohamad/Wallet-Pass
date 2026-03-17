import sys
from pathlib import Path

# Add current project path to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

from wallet_service import WalletClient
import configs

# NOTE: Google Wallet API does NOT support deleting pass objects.
# The only official way to remove a pass from a user's wallet is to set its
# state to EXPIRED, which hides it from the user's active passes.
# Reference: https://developers.google.com/wallet/reference/rest/v1/genericobject

def expire_specific_pass(object_id):
    """
    Expires a single pass by its Object ID by trying all resource types.
    (Google Wallet API does not support deleting passes — EXPIRED is the equivalent.)
    """
    print("=" * 75)
    print(f"🗑️ Attempting to EXPIRE pass: {object_id}")
    print("=" * 75)

    try:
        client = WalletClient()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # List of all possible object methods to try
    methods = [
        client.service.eventticketobject,
        client.service.loyaltyobject,
        client.service.genericobject,
        client.service.giftcardobject,
        client.service.transitobject
    ]

    success = False
    for method in methods:
        try:
            resource = method()
            # First get the object to confirm it exists and grab classId
            obj = resource.get(resourceId=object_id).execute()
            class_id = obj.get('classId')

            # Expire the pass by patching its state
            patch_body = {
                'id': object_id,
                'classId': class_id,
                'state': 'EXPIRED'
            }
            resource.patch(resourceId=object_id, body=patch_body).execute()
            print(f"✅ Success: Pass [{object_id}] expired.")
            success = True
            break
        except Exception:
            continue

    if not success:
        print(f"❌ Failed: Pass ID '{object_id}' was not found or could not be expired.")

    print("=" * 75)
    return success


def expire_all_passes():
    """
    Fetches all classes, finds all associated passes, and expires them all.
    (Google Wallet API does not support deleting passes — EXPIRED is the equivalent.)
    """
    print("=" * 75)
    print("🔥 NUCLEAR OPTION: Expiring ALL passes from Google Wallet")
    print("   (Google Wallet API has no delete — EXPIRED removes them from the wallet)")
    print("=" * 75)

    try:
        client = WalletClient()
        print("✅ Connected to Google API.")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 1. Get all classes registered to the issuer
    print("🔄 Fetching all classes to find associated passes...")
    try:
        all_classes = client.list_all_classes()
        if not all_classes:
            print("⚠️ No classes found. Nothing to expire.")
            return
    except Exception as e:
        print(f"❌ Error fetching classes: {e}")
        return

    total_expired = 0

    resource_map = {
        "EventTicket": client.service.eventticketobject(),
        "LoyaltyCard": client.service.loyaltyobject(),
        "Generic":     client.service.genericobject(),
        "GiftCard":    client.service.giftcardobject(),
        "TransitPass": client.service.transitobject()
    }

    # 2. Iterate through each class to find its objects
    for cls in all_classes:
        class_id   = cls.get('id')
        class_type = cls.get('class_type', 'Generic')
        print(f"\n🔍 Scanning class: {class_id} ({class_type})...")

        resource = resource_map.get(class_type)
        if not resource:
            print(f"   ⚠️ Unknown class type: {class_type}, skipping")
            continue

        try:
            response = resource.list(classId=class_id).execute()

            if 'resources' in response:
                passes = response['resources']
                print(f"   👉 Found {len(passes)} passes. Expiring...")

                for pass_obj in passes:
                    oid = pass_obj['id']
                    try:
                        patch_body = {
                            'id': oid,
                            'classId': class_id,
                            'state': 'EXPIRED'
                        }
                        resource.patch(resourceId=oid, body=patch_body).execute()
                        print(f"      ✅ Expired: {oid}")
                        total_expired += 1
                    except Exception as ex:
                        print(f"      ❌ Failed to expire {oid}: {ex}")
            else:
                print("   (No passes found for this class)")

        except Exception as e:
            print(f"   ❌ Error processing class {class_id}: {e}")

    print("\n" + "=" * 75)
    print(f"🏁 Done. Total passes expired: {total_expired}")
    print("=" * 75)


if __name__ == "__main__":
    print("--- Google Wallet Cleanup Tool ---")
    print("Note: Google Wallet API does not support deleting pass objects.")
    print("      Setting state to EXPIRED is the official removal method.\n")
    print("1. Expire a SPECIFIC pass")
    print("2. Expire ALL passes (Nuclear Option)")

    choice = input("\nSelect an option (1 or 2): ").strip()

    if choice == "1":
        oid = input("Enter the Object ID: ").strip()
        if oid:
            confirm = input(f"⚠️ Expire pass '{oid}'? (y/n): ")
            if confirm.lower() == 'y':
                expire_specific_pass(oid)
        else:
            print("❌ Error: No ID provided.")

    elif choice == "2":
        print("\n⚠️ WARNING: This will expire EVERY pass linked to your account across all classes.")
        confirm = input("Are you ABSOLUTELY sure? This cannot be undone. (yes/no): ")
        if confirm.lower() == 'yes':
            second_confirm = input("Type 'EXPIRE ALL' to confirm: ")
            if second_confirm == 'EXPIRE ALL':
                expire_all_passes()
            else:
                print("❌ Confirmation failed. Operation cancelled.")
        else:
            print("❌ Operation cancelled.")
    else:
        print("❌ Invalid choice.")