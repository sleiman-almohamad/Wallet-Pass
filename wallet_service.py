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
                    # Handle both 404 (not found) and 400 (wrong class type)
                    if e.resp.status in [404, 400]:
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
    
    def list_all_classes(self):
        """
        List all classes from Google Wallet across all class types
        
        Returns:
            List of class objects with their type information
        """
        all_classes = []
        
        # Define class types and their corresponding resources
        class_types = [
            ("Generic", self.service.genericclass()),
            ("LoyaltyCard", self.service.loyaltyclass()),
            ("EventTicket", self.service.eventticketclass()),
            ("GiftCard", self.service.giftcardclass()),
            ("TransitPass", self.service.transitclass()),
        ]
        
        for class_type, resource in class_types:
            try:
                # List classes of this type
                response = resource.list(issuerId=configs.ISSUER_ID).execute()
                
                if 'resources' in response:
                    for cls in response['resources']:
                        # Add class type information
                        cls['class_type'] = class_type
                        all_classes.append(cls)
                        
            except HttpError as e:
                # Skip if this class type has no resources or error
                if e.resp.status != 404:
                    print(f"Warning: Error listing {class_type} classes: {e}")
                continue
        
        return all_classes

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
    
    def create_pass_class(self, class_data, class_type="Generic"):
        """
        Create a pass class (template) in Google Wallet
        
        Args:
            class_data: Dictionary with class data including:
                - id: Class ID (with issuer prefix)
                - issuerName: Name of the issuer
                - reviewStatus: DRAFT or UNDER_REVIEW
                - hexBackgroundColor: Background color
                - logo: Logo image data (optional)
                - heroImage: Hero image data (optional)
            class_type: Type of class (Generic, EventTicket, LoyaltyCard, etc.)
            
        Returns:
            Created class from Google Wallet API
        """
        try:
            # Sanitize reviewStatus field to prevent invalid values
            # Google Wallet only accepts: "UNDER_REVIEW", "DRAFT", or "APPROVED"
            allowed_review_statuses = {"UNDER_REVIEW", "DRAFT", "APPROVED"}
            review_status = class_data.get("reviewStatus")
            
            if isinstance(review_status, str) and review_status not in allowed_review_statuses:
                # Invalid value (e.g., "Optional[APPROVED]"), remove it and use safe default
                print(f"Warning: Invalid reviewStatus '{review_status}' detected, using default 'UNDER_REVIEW'")
                class_data["reviewStatus"] = "UNDER_REVIEW"
            elif review_status is None or review_status == "":
                # Set default if missing
                class_data["reviewStatus"] = "UNDER_REVIEW"
            
            # Select appropriate resource based on class type
            if class_type == "EventTicket":
                resource = self.service.eventticketclass()
            elif class_type == "LoyaltyCard":
                resource = self.service.loyaltyclass()
            elif class_type == "GiftCard":
                resource = self.service.giftcardclass()
            elif class_type == "TransitPass":
                resource = self.service.transitclass()
            else:
                resource = self.service.genericclass()
            
            # Try to insert the class
            return resource.insert(body=class_data).execute()
        except HttpError as e:
            # If class already exists, try to update it
            if e.resp.status == 409:  # Conflict - class already exists
                try:
                    # Use patch instead of update for partial updates (more forgiving)
                    print(f"Class exists, attempting to patch update...")
                    return resource.patch(
                        resourceId=class_data['id'],
                        body=class_data
                    ).execute()
                except HttpError as update_error:
                    # Print detailed error for debugging
                    import json
                    print(f"Error updating class. Class data being sent:")
                    print(json.dumps(class_data, indent=2))
                    error_details = update_error.content.decode('utf-8') if hasattr(update_error, 'content') else str(update_error)
                    print(f"Error details: {error_details}")
                    raise Exception(f"Error updating existing class: {update_error}\n\nClass data: {json.dumps(class_data, indent=2)}")
            else:
                raise Exception(f"Error creating pass class: {e}")
    
    
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
        
        # Read the private key from the service account file
        import json
        with open(configs.KEY_FILE_PATH, 'r') as f:
            service_account_info = json.load(f)
            private_key = service_account_info['private_key']
        
        # Sign the JWT with the service account private key
        token = jwt.encode(
            claims,
            private_key,
            algorithm='RS256'
        )
        
        # Return the Save to Wallet URL
        return f"https://pay.google.com/gp/v/save/{token}"
    
    def update_pass_class(self, class_id, class_data, class_type="Generic"):
        """
        Update an existing pass class in Google Wallet
        
        This triggers automatic push notifications to all users who have
        passes from this class saved in their Google Wallet.
        
        Args:
            class_id: Class ID (with or without issuer prefix)
            class_data: Dictionary with updated class data
            class_type: Type of class (Generic, EventTicket, LoyaltyCard, etc.)
            
        Returns:
            Updated class from Google Wallet API
        """
        try:
            # Ensure class_id has issuer prefix
            full_class_id = self._prepare_ids_to_try(class_id)[0]
            
            # Remove reviewStatus from the update payload to avoid API errors
            # Google Wallet doesn't allow updating reviewStatus on existing classes
            def remove_review_status(obj):
                """Recursively remove reviewStatus from nested dictionaries"""
                if isinstance(obj, dict):
                    obj.pop('reviewStatus', None)
                    for value in obj.values():
                        remove_review_status(value)
                elif isinstance(obj, list):
                    for item in obj:
                        remove_review_status(item)
            
            # Create a copy to avoid modifying the original
            import copy
            clean_class_data = copy.deepcopy(class_data)
            remove_review_status(clean_class_data)
            
            # Select appropriate resource based on class type
            if class_type == "EventTicket":
                resource = self.service.eventticketclass()
            elif class_type == "LoyaltyCard":
                resource = self.service.loyaltyclass()
            elif class_type == "GiftCard":
                resource = self.service.giftcardclass()
            elif class_type == "TransitPass":
                resource = self.service.transitclass()
            else:
                resource = self.service.genericclass()
            
            # Use patch for partial updates (more forgiving than update)
            return resource.patch(
                resourceId=full_class_id,
                body=clean_class_data
            ).execute()
            
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            raise Exception(f"Error updating pass class '{class_id}': {error_details}")
    
    def update_pass_object(self, object_id, class_id, holder_name, holder_email, pass_data, class_type="EventTicket"):
        """
        Update an individual pass object in Google Wallet
        
        This triggers a push notification to the user's device informing them
        that their pass has been updated.
        
        Args:
            object_id: Full object ID (with issuer prefix)
            class_id: Reference class ID (with issuer prefix)
            holder_name: Name of the pass holder
            holder_email: Email of the pass holder
            pass_data: Dictionary with pass-specific data (custom fields)
            class_type: Type of pass (EventTicket, LoyaltyCard, Generic)
            
        Returns:
            Updated object from Google Wallet API
        """
        try:
            # Ensure IDs have issuer prefix
            full_object_id = self._prepare_ids_to_try(object_id)[0]
            full_class_id = self._prepare_ids_to_try(class_id)[0]
            
            # Build the updated pass object using existing builder methods
            if class_type == "EventTicket":
                object_data = self.build_event_ticket_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data
                )
                resource = self.service.eventticketobject()
            elif class_type == "LoyaltyCard":
                object_data = self.build_loyalty_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data
                )
                resource = self.service.loyaltyobject()
            elif class_type == "GiftCard":
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data
                )
                resource = self.service.giftcardobject()
            elif class_type == "TransitPass":
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data
                )
                resource = self.service.transitobject()
            else:  # Generic
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data
                )
                resource = self.service.genericobject()
            
            # Use patch to update the object (more forgiving than full update)
            return resource.patch(
                resourceId=full_object_id,
                body=object_data
            ).execute()
            
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            raise Exception(f"Error updating pass object '{object_id}': {error_details}")
    
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
            if "seat_number" in pass_data or "seat" in pass_data:
                seat_value = pass_data.get("seat_number") or pass_data.get("seat", "")
                obj["seatInfo"] = {
                    "seat": {
                        "defaultValue": {
                            "language": "en-US",
                            "value": str(seat_value)
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
            
            # Add text modules for event details
            text_modules = []
            if "event_name" in pass_data and pass_data["event_name"]:
                text_modules.append({
                    "header": "Event",
                    "body": str(pass_data["event_name"]),
                    "id": "event_info"
                })
            if "event_date" in pass_data and pass_data["event_date"]:
                text_modules.append({
                    "header": "Date",
                    "body": str(pass_data["event_date"]),
                    "id": "event_date"
                })
            
            if text_modules:
                obj["textModulesData"] = text_modules
            
            # Add info modules for all other pass data
            info_label_values = []
            
            # Define which fields to show and their labels
            field_labels = {
                "event_time": "Event Time",
                "seat_number": "Seat",
                "seat": "Seat",
                "section": "Section",
                "row": "Row",
                "gate": "Gate",
                "venue": "Venue"
            }
            
            for field_key, field_label in field_labels.items():
                if field_key in pass_data and pass_data[field_key]:
                    # Skip if already in seatInfo or textModules
                    if field_key in ["event_name", "event_date"]:
                        continue
                    
                    info_label_values.append({
                        "label": field_label,
                        "value": str(pass_data[field_key])
                    })
            
            # Add any additional custom fields not in predefined list
            for key, value in pass_data.items():
                if value and key not in field_labels and key not in ["event_name", "event_date"]:
                    # Format key as label
                    label = key.replace("_", " ").title()
                    info_label_values.append({
                        "label": label,
                        "value": str(value)
                    })
            
            if info_label_values:
                obj["infoModulesData"] = [{
                    "showTime": {},
                    "labelValueRows": [{
                        "columns": info_label_values
                    }]
                }]
        
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
        
        if pass_data:
            # Add loyalty points if available
            if "points_balance" in pass_data or "points" in pass_data:
                points_value = pass_data.get("points_balance") or pass_data.get("points", 0)
                obj["loyaltyPoints"] = {
                    "balance": {
                        "int": int(points_value)
                    }
                }
            
            # Add text modules for member information
            text_modules = []
            if "member_since" in pass_data and pass_data["member_since"]:
                text_modules.append({
                    "header": "Member Since",
                    "body": str(pass_data["member_since"]),
                    "id": "member_info"
                })
            
            if text_modules:
                obj["textModulesData"] = text_modules
            
            # Add info modules for tier and other details
            info_label_values = []
            
            # Define which fields to show and their labels
            field_labels = {
                "tier_level": "Tier",
                "tier": "Tier",
                "points_balance": "Points Balance",
                "points": "Points",
                "rewards_available": "Available Rewards",
                "expiry_date": "Expires"
            }
            
            for field_key, field_label in field_labels.items():
                if field_key in pass_data and pass_data[field_key]:
                    # Skip member_since as it's in textModules
                    if field_key == "member_since":
                        continue
                    
                    info_label_values.append({
                        "label": field_label,
                        "value": str(pass_data[field_key])
                    })
            
            # Add any additional custom fields
            for key, value in pass_data.items():
                if value and key not in field_labels and key != "member_since":
                    label = key.replace("_", " ").title()
                    info_label_values.append({
                        "label": label,
                        "value": str(value)
                    })
            
            if info_label_values:
                obj["infoModulesData"] = [{
                    "showTime": {},
                    "labelValueRows": [{
                        "columns": info_label_values
                    }]
                }]
        
        return obj
    
    def build_generic_object(self, object_id, class_id, holder_name, holder_email, pass_data):
        """Build a Generic object structure"""
        # Get cardTitle from pass_data, fallback to holder_name
        card_title_value = pass_data.get("header_value", holder_name) if pass_data else holder_name
        
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "header": {
                "defaultValue": {
                    "language": "en-US",
                    "value": holder_name
                }
            },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": card_title_value
                }
            }
        }
        
        if pass_data:
            # Add subheader if provided
            if "subheader" in pass_data and pass_data["subheader"]:
                obj["subheader"] = {
                    "defaultValue": {
                        "language": "en-US",
                        "value": pass_data["subheader"]
                    }
                }
            
            # Add text modules for any text-heavy fields
            text_modules = []
            if "description" in pass_data and pass_data["description"]:
                text_modules.append({
                    "header": "Description",
                    "body": str(pass_data["description"]),
                    "id": "description"
                })
            
            if text_modules:
                obj["textModulesData"] = text_modules
            
            # Add info modules for all other data
            info_label_values = []
            
            # Skip fields already used in header, cardTitle, subheader, or textModules
            skip_fields = ["header_value", "subheader", "description"]
            
            for key, value in pass_data.items():
                if value and key not in skip_fields:
                    # Format key as label
                    label = key.replace("_", " ").title()
                    info_label_values.append({
                        "label": label,
                        "value": str(value)
                    })
            
            if info_label_values:
                obj["infoModulesData"] = [{
                    "showTime": {},
                    "labelValueRows": [{
                        "columns": info_label_values
                    }]
                }]
        
        return obj