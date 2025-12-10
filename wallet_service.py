import json 
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import configs
import jwt
from datetime import datetime, timedelta

class WalletClient:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """
        Authenticates with Google using the service account file.
        Handles file path fallback if the default name is not found.
        """
        
        # Check if the key file exists at the default path
        if not os.path.exists(configs.KEY_FILE_PATH):
            # Try the alternative file name commonly used in your project
            if os.path.exists(configs.KEY_FILE_PATH):
                configs.KEY_FILE_PATH = configs.KEY_FILE_PATH
            else:
                raise FileNotFoundError(f"Credentials file not found: {configs.KEY_FILE_PATH}")
            
        self.credentials = service_account.Credentials.from_service_account_file(
            configs.KEY_FILE_PATH, scopes=configs.SCOPES)
        self.service = build('walletobjects', 'v1', credentials=self.credentials)

    def _prepare_ids_to_try(self, input_id):
        """
        Smart helper to prepare a list of potential Resource IDs.
        Automatically handles the Issuer ID prefix logic.
        """
        clean_id = input_id.strip()
        ids = []

        # 1. Ideal scenario: The input ID already starts with the Issuer ID
        if clean_id.startswith(configs.ISSUER_ID):
            ids.append(clean_id)
        
        # 2. Common scenario: User entered only the Suffix (Name)
        else:
            # Priority 1: Try constructing the valid ID (Issuer.Suffix)
            ids.append(f"{configs.ISSUER_ID}.{clean_id}")
            # Priority 2: Try the raw input just in case (fallback)
            ids.append(clean_id)
            
        return ids

    def get_object(self, object_id):
        """
        Iterates through all possible Object types (Loyalty, Generic, Event, etc.)
        to find a match for the given Object ID.
        """
        resources = [
            self.service.genericobject(),
            self.service.loyaltyobject(),
            self.service.offerobject(),
            self.service.giftcardobject(),
            self.service.transitobject(),
            self.service.flightobject(),
            self.service.eventticketobject()
        ]

        # Prepare ID variations (Raw vs Prefixed)
        ids_to_try = self._prepare_ids_to_try(object_id)
        
        last_error = None
        
        for oid in ids_to_try:
            # Optional: print(f"Trying Object ID: {oid}") 
            for resource in resources:
                try:
                    return resource.get(resourceId=oid).execute()
                except HttpError as e:
                    if e.resp.status == 404:
                        last_error = e
                        continue
                    else:
                        raise e
            
        if last_error:
            raise last_error
        else:
             raise Exception("Unknown error fetching object")

    def get_class(self, class_id):
        """
        Iterates through all possible Class types (Templates) 
        to find a match for the given Class ID.
        """
        resources = [
            self.service.genericclass(),
            self.service.loyaltyclass(),
            self.service.offerclass(),
            self.service.giftcardclass(),
            self.service.transitclass(),
            self.service.flightclass(),
            self.service.eventticketclass()
        ]

        # Prepare ID variations (Raw vs Prefixed)
        ids_to_try = self._prepare_ids_to_try(class_id)
        last_error = None

        for cid in ids_to_try:
            print(f"Trying Class ID: {cid}")
            for resource in resources:
                try:
                    return resource.get(resourceId=cid).execute()
                except HttpError as e:
                    if e.resp.status == 404:
                        last_error = e
                        continue
                    else:
                        raise e
        
        if last_error:
            # Decode error content for better debugging in the UI
            error_content = last_error.content.decode('utf-8') if hasattr(last_error, 'content') else str(last_error)
            raise Exception(f"Google Error (404): Class not found.\nTried IDs: {ids_to_try}\nDetails: {error_content}")
        else:
             raise Exception("Unknown error fetching class")

    def verify_pass(self, object_id):
        """
        Orchestrates the verification process:
        1. Fetches the User Object (Pass).
        2. Extracts the linked Class ID.
        3. Fetches the Class Template details.
        """
        try:
            print(f"Fetching object: {object_id}")
            wallet_object = self.get_object(object_id)
            
            class_id = wallet_object.get('classId')
            if not class_id:
                return {"error": "No classId found in the object."}
            
            print(f"Found Class ID: {class_id}")
            wallet_class = self.get_class(class_id)
            
            return {
                "object": wallet_object,
                "class": wallet_class
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_pass_object(self, object_data, class_type="EventTicket"):
        """
        Create a pass object in Google Wallet
        
        Args:
            object_data: Dictionary with pass object data
            class_type: Type of pass (EventTicket, LoyaltyCard, etc.)
            
        Returns:
            Created object from Google Wallet API
        """
        try:
            # Select appropriate resource based on class type
            if class_type == "EventTicket":
                resource = self.service.eventticketobject()
            elif class_type == "LoyaltyCard":
                resource = self.service.loyaltyobject()
            elif class_type == "GiftCard":
                resource = self.service.giftcardobject()
            elif class_type == "TransitPass":
                resource = self.service.transitobject()
            else:
                resource = self.service.genericobject()
            
            return resource.insert(body=object_data).execute()
        except HttpError as e:
            raise Exception(f"Error creating pass object: {e}")
    
    def generate_save_link(self, object_id, class_type="EventTicket"):
        """
        Generate a "Save to Google Wallet" link with JWT token
        
        Args:
            object_id: The pass object ID
            class_type: Type of pass
            
        Returns:
            URL that can be used to add pass to Google Wallet
        """
        # Determine the payload key based on class type
        payload_key_map = {
            "EventTicket": "eventTicketObjects",
            "LoyaltyCard": "loyaltyObjects",
            "GiftCard": "giftCardObjects",
            "TransitPass": "transitObjects",
            "Generic": "genericObjects"
        }
        
        payload_key = payload_key_map.get(class_type, "genericObjects")
        
        # Create JWT claims
        claims = {
            "iss": self.credentials.service_account_email,
            "aud": "google",
            "origins": [],
            "typ": "savetowallet",
            "iat": datetime.utcnow(),
            "payload": {
                payload_key: [{
                    "id": object_id
                }]
            }
        }
        
        # Sign the JWT with the service account private key
        token = jwt.encode(
            claims,
            self.credentials.signer.key_bytes,
            algorithm='RS256'
        )
        
        # Return the Save to Wallet URL
        return f"https://pay.google.com/gp/v/save/{token}"
    
    def build_event_ticket_object(self, object_id, class_id, holder_name, holder_email, pass_data):
        """
        Build an EventTicket object structure for Google Wallet
        
        Args:
            object_id: Unique object ID
            class_id: Reference to class
            holder_name: Holder's name
            holder_email: Holder's email
            pass_data: Dictionary with pass-specific data (seat, gate, etc.)
            
        Returns:
            Dictionary formatted for Google Wallet API
        """
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "ticketHolderName": holder_name,
            "reservationInfo": {
                "confirmationCode": object_id.split('.')[-1] if '.' in object_id else object_id
            }
        }
        
        # Add seat information if available
        if pass_data:
            if "seat" in pass_data:
                obj["seatInfo"] = {
                    "seat": {
                        "defaultValue": {
                            "language": "en-US",
                            "value": str(pass_data["seat"])
                        }
                    }
                }
            if "gate" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["gate"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": str(pass_data["gate"])
                    }
                }
            if "row" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["row"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": str(pass_data["row"])
                    }
                }
            if "section" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["section"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": str(pass_data["section"])
                    }
                }
        
        return obj
    
    def build_loyalty_object(self, object_id, class_id, holder_name, holder_email, pass_data):
        """Build a LoyaltyCard object structure"""
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "accountName": holder_name,
            "accountId": holder_email
        }
        
        if pass_data and "points" in pass_data:
            obj["loyaltyPoints"] = {
                "balance": {
                    "int": int(pass_data["points"])
                }
            }
        
        return obj
    
    def build_generic_object(self, object_id, class_id, holder_name, holder_email, pass_data):
        """Build a Generic object structure"""
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": holder_name
                }
            }
        }
        
        return obj