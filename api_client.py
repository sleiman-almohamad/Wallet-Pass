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
                    logo_url: Optional[str] = None,
                    issuer_name: Optional[str] = None,
                    header_text: Optional[str] = None,
                    card_title: Optional[str] = None,
                    class_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new class"""
        data = {
            "class_id": class_id,
            "class_type": class_type,
            "base_color": base_color,
            "logo_url": logo_url,
            "issuer_name": issuer_name,
            "header_text": header_text,
            "card_title": card_title,
            "class_json": class_json
        }
        try:
            response = requests.post(f"{self.base_url}/classes/", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error creating class: {e}")
    
    def update_class(self, class_id: str, 
                    class_type: Optional[str] = None,
                    base_color: Optional[str] = None, 
                    logo_url: Optional[str] = None,
                    issuer_name: Optional[str] = None,
                    header_text: Optional[str] = None,
                    card_title: Optional[str] = None,
                    class_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing class"""
        data = {}
        if class_type is not None:
            data["class_type"] = class_type
        if base_color is not None:
            data["base_color"] = base_color
        if logo_url is not None:
            data["logo_url"] = logo_url
        if issuer_name is not None:
            data["issuer_name"] = issuer_name
        if header_text is not None:
            data["header_text"] = header_text
        if card_title is not None:
            data["card_title"] = card_title
        if class_json is not None:
            data["class_json"] = class_json
        
        try:
            response = requests.put(f"{self.base_url}/classes/{class_id}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error updating class: {e}")

    
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
    
    def update_pass(self, object_id: str, 
                    holder_name: Optional[str] = None,
                    holder_email: Optional[str] = None,
                    status: Optional[str] = None,
                    pass_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing pass"""
        data = {}
        if holder_name is not None:
            data["holder_name"] = holder_name
        if holder_email is not None:
            data["holder_email"] = holder_email
        if status is not None:
            data["status"] = status
        if pass_data is not None:
            data["pass_data"] = pass_data
        
        try:
            response = requests.put(f"{self.base_url}/passes/{object_id}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise Exception(f"Error updating pass: {error_detail}")
        except Exception as e:
            raise Exception(f"Error updating pass: {e}")

    def sync_classes(self) -> Dict[str, Any]:
        """Trigger sync of all classes from Google Wallet to local database"""
        try:
            response = requests.post(f"{self.base_url}/classes/sync")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise Exception(f"Sync failed: {error_detail}")
        except Exception as e:
            raise Exception(f"Sync failed: {e}")

    def sync_passes(self) -> Dict[str, Any]:
        """Trigger sync of all pass objects from Google Wallet to local database"""
        try:
            response = requests.post(f"{self.base_url}/passes/sync")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise Exception(f"Sync passes failed: {error_detail}")
        except Exception as e:
            raise Exception(f"Sync passes failed: {e}")

    def check_health(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
