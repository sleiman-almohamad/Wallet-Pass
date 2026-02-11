
from wallet_service import WalletClient
from unittest.mock import MagicMock

# Mock the Google API service
mock_service = MagicMock()
mock_resource = MagicMock()
mock_service.genericclass.return_value = mock_resource

# Instantiate WalletClient with mocked service
client = WalletClient()
client.service = mock_service

# Test data with reviewStatus
class_data = {
    "id": "123",
    "reviewStatus": "UNDER_REVIEW",
    "nested": {
        "reviewStatus": "DRAFT",
        "value": "keep me"
    }
}

# Call update_pass_class
try:
    client.update_pass_class("123", class_data, "Generic")
except Exception as e:
    print(f"Error during test: {e}")

# Verify what was sent to the API
# args[0] is typically resourceId, args[1] is body (or kwargs)
call_args = mock_resource.patch.call_args
if call_args:
    _, kwargs = call_args
    sent_body = kwargs.get('body')
    
    print("Sent Body:")
    import json
    print(json.dumps(sent_body, indent=2))
    
    if "reviewStatus" in sent_body:
        print("\n❌ FAILED: reviewStatus found in top level")
    elif "reviewStatus" in sent_body.get("nested", {}):
         print("\n❌ FAILED: reviewStatus found in nested level")
    else:
        print("\n✅ SUCCESS: reviewStatus successfully removed from payload")
else:
    print("\n❌ FAILED: API patch method was not called")
