import sys
import os
from unittest.mock import MagicMock, patch
import json

# Add project root to path
sys.path.append(os.getcwd())

# Mock dependencies before importing api
sys.modules['database.db_manager'] = MagicMock()
sys.modules['wallet_service'] = MagicMock()
sys.modules['services.class_update_service'] = MagicMock()
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = MagicMock()

# Now import the necessary modules
from api.api import app, db, wallet_client
from api.models import PassUpdate, PassStatus

def test_sync_passes():
    print("Testing /passes/sync...")
    
    # Mock wallet_client.list_all_pass_objects
    mock_pass = {
        'id': '3388000000023033675.TestPass',
        'classId': '3388000000023033675.TestClass',
        'ticketHolderName': 'John Doe',
        'accountId': 'john@example.com',
        'state': 'ACTIVE'
    }
    wallet_client.list_all_pass_objects.return_value = [mock_pass]
    
    # Mock db.get_pass (not found) and db.get_class (found)
    db.get_pass.return_value = None
    db.get_class.return_value = {'class_id': 'TestClass'}
    
    # Test sync
    import asyncio
    async def run_sync():
        return await app.router.app_all['sync_passes']() # This is manual call, simpler to use httpx in real test
    
    # Actually let's just test the logic inside the function if possible, or use a TestClient
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.post("/passes/sync")
    print(f"Sync Response: {response.json()}")
    
    assert response.status_code == 200
    assert "Sync complete" in response.json()['message']
    db.create_pass.assert_called_once()
    print("✅ Sync passes test passed!")

def test_update_pass():
    print("\nTesting /passes/{object_id} PUT...")
    
    object_id = "3388000000023033675.TestPass"
    db.get_pass.return_value = {
        'object_id': object_id,
        'class_id': 'TestClass',
        'holder_name': 'John Doe',
        'holder_email': 'john@example.com',
        'status': 'Active',
        'pass_data': {}
    }
    db.get_class.return_value = {'class_id': 'TestClass', 'class_type': 'Generic'}
    db.update_pass.return_value = True
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    update_data = {
        "holder_name": "Jane Doe",
        "pass_data": {"new_field": "value"}
    }
    
    response = client.put(f"/passes/{object_id}", json=update_data)
    print(f"Update Response: {response.json()}")
    
    assert response.status_code == 200
    assert "updated successfully" in response.json()['message']
    wallet_client.update_pass_object.assert_called_once()
    print("✅ Update pass test passed!")

if __name__ == "__main__":
    try:
        # Install httpx if needed
        # import httpx
        test_sync_passes()
        test_update_pass()
        print("\nAll verification tests passed!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
