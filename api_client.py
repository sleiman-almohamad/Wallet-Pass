"""
API Client Helper for Wallet Passes
Provides functions to interact with the FastAPI backend
"""

import requests
from typing import List, Dict, Any, Optional


class APIClient:
    """Client for interacting with Wallet Passes API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get_classes(self) -> List[Dict[str, Any]]:
        """Fetch all available classes"""
        try:
            response = requests.get(f"{self.base_url}/classes/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching classes: {e}")
            return []
    
    def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific class by ID"""
        try:
            response = requests.get(f"{self.base_url}/classes/{class_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching class: {e}")
            return None
    
    def create_class(self, class_id: str, class_type: str, 
                    base_color: Optional[str] = None, 
                    logo_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new class"""
        data = {
            "class_id": class_id,
            "class_type": class_type,
            "base_color": base_color,
            "logo_url": logo_url
        }
        try:
            response = requests.post(f"{self.base_url}/classes/", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error creating class: {e}")
    
    def create_pass(self, object_id: str, class_id: str, 
                   holder_name: str, holder_email: str,
                   status: str = "Active",
                   pass_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new pass"""
        data = {
            "object_id": object_id,
            "class_id": class_id,
            "holder_name": holder_name,
            "holder_email": holder_email,
            "status": status,
            "pass_data": pass_data or {}
        }
        try:
            response = requests.post(f"{self.base_url}/passes/", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise Exception(f"Error creating pass: {error_detail}")
        except Exception as e:
            raise Exception(f"Error creating pass: {e}")
    
    def get_passes(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all passes, optionally filtered by status"""
        try:
            url = f"{self.base_url}/passes/"
            if status:
                url += f"?status={status}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching passes: {e}")
            return []
    
    def get_pass(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific pass by object ID"""
        try:
            response = requests.get(f"{self.base_url}/passes/{object_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching pass: {e}")
            return None
    
    def check_health(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
