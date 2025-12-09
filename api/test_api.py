"""
Simple test script to verify API functionality
Run this from the project root directory
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_create_class():
    """Test creating a class"""
    print("Testing create class...")
    data = {
        "class_id": "TEST_EVENT_001",
        "class_type": "EventTicket",
        "base_color": "#FF5733",
        "logo_url": "https://example.com/logo.png"
    }
    response = requests.post(f"{BASE_URL}/classes/", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_get_classes():
    """Test getting all classes"""
    print("Testing get all classes...")
    response = requests.get(f"{BASE_URL}/classes/")
    print(f"Status: {response.status_code}")
    print(f"Found {len(response.json())} classes\n")

def test_create_pass():
    """Test creating a pass"""
    print("Testing create pass...")
    data = {
        "object_id": "TEST_PASS_001",
        "class_id": "TEST_EVENT_001",
        "holder_name": "Test User",
        "holder_email": "test@example.com",
        "status": "Active",
        "pass_data": {
            "seat": "A12",
            "gate": "Gate 5"
        }
    }
    response = requests.post(f"{BASE_URL}/passes/", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_get_passes():
    """Test getting all passes"""
    print("Testing get all passes...")
    response = requests.get(f"{BASE_URL}/passes/")
    print(f"Status: {response.status_code}")
    print(f"Found {len(response.json())} passes\n")

if __name__ == "__main__":
    print("=" * 50)
    print("Wallet Passes API Test Suite")
    print("=" * 50 + "\n")
    
    try:
        test_health()
        test_create_class()
        test_get_classes()
        test_create_pass()
        test_get_passes()
        print("✓ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")
