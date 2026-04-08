"""
API Client Helper for Wallet Passes
Provides functions to interact with the FastAPI backend
"""

import requests
from typing import List, Dict, Any, Optional
from exceptions import APIClientHTTPError, APIClientError


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
                    issuer_name: Optional[str] = None,
                    base_color: Optional[str] = None, 
                    logo_url: Optional[str] = None,
                    hero_image_url: Optional[str] = None,
                    header_text: Optional[str] = None,
                    card_title: Optional[str] = None,
                    event_name: Optional[str] = None,
                    venue_name: Optional[str] = None,
                    venue_address: Optional[str] = None,
                    event_start: Optional[str] = None,
                    program_name: Optional[str] = None,
                    transit_type: Optional[str] = None,
                    transit_operator_name: Optional[str] = None,
                    class_json: Optional[Dict[str, Any]] = None,
                    multiple_devices_allowed: Optional[str] = None,
                    view_unlock_requirement: Optional[str] = None,
                    enable_smart_tap: Optional[bool] = None,
                    text_module_rows: Optional[list] = None,
                    **extra) -> Dict[str, Any]:
        """Create a new class"""
        data = {
            "class_id": class_id,
            "class_type": class_type,
            "issuer_name": issuer_name,
            "base_color": base_color,
            "logo_url": logo_url,
            "hero_image_url": hero_image_url,
            "header_text": header_text,
            "card_title": card_title,
            "event_name": event_name,
            "venue_name": venue_name,
            "venue_address": venue_address,
            "event_start": event_start,
            "program_name": program_name,
            "transit_type": transit_type,
            "transit_operator_name": transit_operator_name,
            "class_json": class_json,
            "multiple_devices_allowed": multiple_devices_allowed,
            "view_unlock_requirement": view_unlock_requirement,
            "enable_smart_tap": enable_smart_tap,
            "text_module_rows": text_module_rows
        }
        # filter out Nones
        data = {k: v for k, v in data.items() if v is not None}
        try:
            response = requests.post(f"{self.base_url}/classes/", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            raise APIClientHTTPError(
                f"HTTP Error creating class. Detail: {error_detail}. Status: {response.status_code}. Data: {data}",
                status_code=response.status_code,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error creating class: {e}") from e
    
    def update_class(self, class_id: str, 
                    class_type: Optional[str] = None,
                    issuer_name: Optional[str] = None,
                    base_color: Optional[str] = None, 
                    logo_url: Optional[str] = None,
                    hero_image_url: Optional[str] = None,
                    header_text: Optional[str] = None,
                    card_title: Optional[str] = None,
                    event_name: Optional[str] = None,
                    venue_name: Optional[str] = None,
                    venue_address: Optional[str] = None,
                    event_start: Optional[str] = None,
                    program_name: Optional[str] = None,
                    transit_type: Optional[str] = None,
                    transit_operator_name: Optional[str] = None,
                    class_json: Optional[Dict[str, Any]] = None,
                    multiple_devices_allowed: Optional[str] = None,
                    view_unlock_requirement: Optional[str] = None,
                    enable_smart_tap: Optional[bool] = None,
                    text_module_rows: Optional[list] = None,
                    sync_to_google: bool = True,
                    notification_message: Optional[str] = None,
                    **extra) -> Dict[str, Any]:
        """Update an existing class"""
        data = {}
        for field_name, field_val in [
            ("class_type", class_type), ("issuer_name", issuer_name),
            ("base_color", base_color), ("logo_url", logo_url),
            ("hero_image_url", hero_image_url), ("header_text", header_text),
            ("card_title", card_title), ("event_name", event_name),
            ("venue_name", venue_name), ("venue_address", venue_address),
            ("event_start", event_start), ("program_name", program_name),
            ("transit_type", transit_type), ("transit_operator_name", transit_operator_name),
            ("class_json", class_json), ("multiple_devices_allowed", multiple_devices_allowed),
            ("view_unlock_requirement", view_unlock_requirement), ("enable_smart_tap", enable_smart_tap),
            ("text_module_rows", text_module_rows)
        ]:
            if field_val is not None:
                data[field_name] = field_val
        
        try:
            params = {"sync_to_google": sync_to_google}
            if notification_message:
                params["notification_message"] = notification_message
            
            response = requests.put(
                f"{self.base_url}/classes/{class_id}",
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            raise APIClientHTTPError(
                f"HTTP Error updating class. Detail: {error_detail}. Status: {response.status_code}. Data: {data}",
                status_code=response.status_code,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error updating class: {e}") from e

    def create_apple_pass(self, serial_number: str, template_id: str, 
                          pass_type_id: str, holder_name: str, 
                          holder_email: str, auth_token: str,
                          status: str = "Active",
                          pass_data: Optional[Dict[str, Any]] = None,
                          store_card_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new Apple Wallet pass locally"""
        data = {
            "serial_number": serial_number,
            "template_id": template_id,
            "pass_type_id": pass_type_id,
            "holder_name": holder_name,
            "holder_email": holder_email,
            "auth_token": auth_token,
            "status": status,
            "pass_data": pass_data or {},
            "store_card_data": store_card_data or {}
        }
        try:
            response = requests.post(f"{self.base_url}/passes/apple/", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error creating Apple pass: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error creating Apple pass: {e}") from e

    
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
            raise APIClientHTTPError(
                f"Error creating pass: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error creating pass: {e}") from e
    
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

    def get_passes_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """Fetch all passes belonging to a specific class (from local DB)"""
        try:
            response = requests.get(f"{self.base_url}/passes/class/{class_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching passes for class '{class_id}': {e}")
            return []

    def get_passes_by_email(self, email: str) -> List[Dict[str, Any]]:
        """Fetch all passes belonging to a specific email (from local DB)"""
        try:
            from urllib.parse import quote
            safe_email = quote(email)
            response = requests.get(f"{self.base_url}/passes/email/{safe_email}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching passes for email '{email}': {e}")
            return []



    def get_passes_by_class_from_google(self, class_id: str) -> List[Dict[str, Any]]:
        """Fetch all passes for a class LIVE from Google Wallet API (no local DB)"""
        try:
            response = requests.get(f"{self.base_url}/passes/google/class/{class_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching passes from Google Wallet for class '{class_id}': {e}")
            return []

    def get_pass_from_google(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single pass LIVE from Google Wallet API (no local DB)"""
        try:
            response = requests.get(f"{self.base_url}/passes/google/object/{object_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching pass '{object_id}' from Google Wallet: {e}")
            return None


    def update_pass(self, object_id: str, 
                    holder_name: Optional[str] = None,
                    holder_email: Optional[str] = None,
                    status: Optional[str] = None,
                    pass_data: Optional[Dict[str, Any]] = None,
                    sync_to_google: bool = True) -> Dict[str, Any]:
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
        
        url = f"{self.base_url}/passes/{object_id}?sync_to_google={'true' if sync_to_google else 'false'}"
        try:
            response = requests.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error updating pass: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error updating pass: {e}") from e

    def generate_save_link(self, object_id: str) -> str:
        """Generate a Google Wallet JWT save link for a given pass"""
        try:
            response = requests.get(f"{self.base_url}/passes/{object_id}/save-link")
            response.raise_for_status()
            return response.json().get("save_link", "")
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error generating save link: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error generating save link: {e}") from e

    def push_pass_to_google(self, object_id: str) -> Dict[str, Any]:
        """Push a pass to Google Wallet using the local database state"""
        try:
            response = requests.post(f"{self.base_url}/passes/{object_id}/push")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error pushing pass to Google: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Error pushing pass to Google: {e}") from e

    def sync_classes(self) -> Dict[str, Any]:
        """Trigger sync of all classes from Google Wallet to local database"""
        try:
            response = requests.post(f"{self.base_url}/classes/sync")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Sync failed: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Sync failed: {e}") from e

    def sync_passes(self) -> Dict[str, Any]:
        """Trigger sync of all pass objects from Google Wallet to local database"""
        try:
            response = requests.post(f"{self.base_url}/passes/sync")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Sync passes failed: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Sync passes failed: {e}") from e

    def check_health(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def send_pass_notification(self, object_id: str, message: str) -> Dict[str, Any]:
        """Send a push notification to a specific pass holder"""
        try:
            response = requests.post(
                f"{self.base_url}/passes/{object_id}/notify",
                json={"message": message}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error sending pass notification: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except Exception as e:
            raise APIClientError(f"Error sending pass notification: {e}") from e


    def send_class_notification(self, class_id: str, message: str) -> Dict[str, Any]:
        """Send a push notification to all holders of a template/class"""
        try:
            response = requests.post(
                f"{self.base_url}/classes/{class_id}/notify",
                json={"message": message}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(
                f"Error sending bulk notification: {error_detail}",
                status_code=e.response.status_code if e.response else None,
                detail=str(error_detail),
            ) from e
        except Exception as e:
            raise APIClientError(f"Error sending bulk notification: {e}") from e

    # ========================================================================
    # Apple Template Endpoints
    # ========================================================================

    def get_apple_templates(self) -> List[Dict[str, Any]]:
        """Fetch all available Apple Wallet templates"""
        try:
            response = requests.get(f"{self.base_url}/templates/apple/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching apple templates: {e}")
            return []

    def get_apple_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific Apple template by ID"""
        try:
            response = requests.get(f"{self.base_url}/templates/apple/{template_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching apple template '{template_id}': {e}")
            return None

    def create_apple_template(self, template_id: str, template_name: str, 
                             pass_style: str, pass_type_identifier: str, 
                             team_identifier: str) -> Dict[str, Any]:
        """Create a new Apple Wallet template"""
        data = {
            "template_id": template_id,
            "template_name": template_name,
            "pass_style": pass_style,
            "pass_type_identifier": pass_type_identifier,
            "team_identifier": team_identifier
        }
        try:
            response = requests.post(f"{self.base_url}/templates/apple/", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(f"Error creating Apple template: {error_detail}") from e
        except Exception as e:
            raise APIClientError(f"Error creating Apple template: {e}") from e

    def update_apple_template(self, template_id: str, **kwargs) -> Dict[str, Any]:
        """Update an existing Apple Wallet template"""
        try:
            response = requests.put(f"{self.base_url}/templates/apple/{template_id}", json=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(f"Error updating Apple template: {error_detail}") from e
        except Exception as e:
            raise APIClientError(f"Error updating Apple template: {e}") from e

    def delete_apple_template(self, template_id: str) -> Dict[str, Any]:
        """Delete an Apple Wallet template"""
        try:
            response = requests.delete(f"{self.base_url}/templates/apple/{template_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(f"Error deleting Apple template: {error_detail}") from e
        except Exception as e:
            raise APIClientError(f"Error deleting Apple template: {e}") from e

    # ========================================================================
    # Apple Pass Endpoints
    # ========================================================================

    def get_all_apple_passes(self) -> List[Dict[str, Any]]:
        """Fetch all Apple Wallet passes"""
        try:
            response = requests.get(f"{self.base_url}/passes/apple/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching apple passes: {e}")
            return []

    def get_apple_pass(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific Apple pass by serial number"""
        try:
            response = requests.get(f"{self.base_url}/passes/apple/{serial_number}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching apple pass '{serial_number}': {e}")
            return None

    def update_apple_pass(self, serial_number: str, **kwargs) -> Dict[str, Any]:
        """Update an existing Apple Wallet pass"""
        try:
            response = requests.put(f"{self.base_url}/passes/apple/{serial_number}", json=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e))
            raise APIClientHTTPError(f"Error updating Apple pass: {error_detail}") from e
        except Exception as e:
            raise APIClientError(f"Error updating Apple pass: {e}") from e

