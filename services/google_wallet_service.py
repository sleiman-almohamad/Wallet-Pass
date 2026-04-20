import json 
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import configs
from exceptions import GoogleWalletAPIError, GoogleWalletNotFoundError, GoogleWalletError
import jwt
from datetime import datetime, timedelta

class WalletClient:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()

    def _list_all_pages(self, list_method, **kwargs):
        """
        Exhaust a Google Wallet `list()` method by following nextPageToken.

        Args:
            list_method: bound googleapiclient list method (e.g., resource.list)
            **kwargs: parameters passed to list()

        Returns:
            List of resource dicts aggregated across all pages.
        """
        all_resources = []
        page_token = None

        while True:
            if page_token:
                kwargs["pageToken"] = page_token
            else:
                # Ensure we don't accidentally reuse an old token
                kwargs.pop("pageToken", None)

            resp = list_method(**kwargs).execute()
            all_resources.extend(resp.get("resources", []) or [])

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return all_resources

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
             raise GoogleWalletNotFoundError("Unknown error fetching object")

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
            raise GoogleWalletNotFoundError(f"Google Error (404): Class not found.\nTried IDs: {ids_to_try}\nDetails: {error_content}")
        else:
             raise GoogleWalletNotFoundError("Unknown error fetching class")
    
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
            ("Offer", self.service.offerclass()),
            ("Flight", self.service.flightclass()),
        ]
        
        for class_type, resource in class_types:
            try:
                # List classes of this type
                classes = self._list_all_pages(resource.list, issuerId=configs.ISSUER_ID)
                for cls in classes:
                    # Add class type information
                    cls['class_type'] = class_type
                    all_classes.append(cls)
                        
            except HttpError as e:
                # Skip if this class type has no resources or error
                if e.resp.status != 404:
                    print(f"Warning: Error listing {class_type} classes: {e}")
                continue
        
        return all_classes

    def list_all_pass_objects(self):
        """
        List all pass objects from Google Wallet across all object types
        
        This method first fetches all classes, then for each class it fetches
        the associated pass objects. This is more reliable than trying to list
        all objects without filtering by class.
        
        Returns:
            List of pass objects with their type information
        """
        all_objects = []
        
        # Step 1: Get all classes to know which ones exist
        try:
            all_classes = self.list_all_classes()
            print(f"DEBUG: Found {len(all_classes)} classes to check for objects")
        except Exception as e:
            print(f"ERROR: Failed to fetch classes: {e}")
            return []
        
        # Step 2: For each class, fetch its objects
        for cls in all_classes:
            class_id = cls.get('id')
            class_type = cls.get('class_type', 'Generic')
            
            # Map class type to the appropriate resource
            resource_map = {
                "EventTicket": self.service.eventticketobject(),
                "LoyaltyCard": self.service.loyaltyobject(),
                "Generic": self.service.genericobject(),
                "GiftCard": self.service.giftcardobject(),
                "TransitPass": self.service.transitobject()
                ,
                "Offer": self.service.offerobject(),
                "Flight": self.service.flightobject(),
            }
            
            resource = resource_map.get(class_type)
            if not resource:
                print(f"DEBUG: Unknown class type '{class_type}' for class {class_id}, skipping")
                continue
            
            try:
                # List objects for this specific class
                print(f"DEBUG: Listing {class_type} objects for class {class_id}...")
                objs = self._list_all_pages(resource.list, classId=class_id)
                count = len(objs)
                print(f"DEBUG: Found {count} {class_type} objects for class {class_id}")
                for obj in objs:
                    # Add object type information
                    obj['class_type'] = class_type
                    all_objects.append(obj)
                        
            except HttpError as e:
                # Skip if this class has no objects or error
                if e.resp.status != 404:
                    print(f"Warning: Error listing {class_type} objects for class {class_id}: {e}")
                continue
            except Exception as e:
                print(f"Error listing {class_type} objects for class {class_id}: {e}")
                continue
        
        print(f"DEBUG: Total objects found across all classes: {len(all_objects)}")
        return all_objects


    def list_class_objects(self, class_id):
        """
        List all pass objects for a specific class ID
        
        Args:
            class_id: Class ID (with or without issuer prefix)
            
        Returns:
            List of pass objects (with 'id' and 'resource' keys) that belong to this class
        """
        # Ensure class_id has issuer prefix
        full_class_id = self._prepare_ids_to_try(class_id)[0]
        
        # Define object types and their corresponding resources
        object_types = [
            ("Generic", self.service.genericobject()),
            ("LoyaltyCard", self.service.loyaltyobject()),
            ("EventTicket", self.service.eventticketobject()),
            ("GiftCard", self.service.giftcardobject()),
            ("TransitPass", self.service.transitobject()),
            ("Offer", self.service.offerobject()),
            ("Flight", self.service.flightobject()),
        ]
        
        matching_objects = []
        
        for obj_type, resource in object_types:
            try:
                # List objects of this type with pagination, filtered by class ID
                print(f"DEBUG: Attempting to list {obj_type} objects for class {full_class_id}...")
                objs = self._list_all_pages(resource.list, classId=full_class_id)
                for obj in objs:
                    matching_objects.append({
                        'id': obj['id'],
                        'resource': resource,
                        'class_type': obj_type,
                        'data': obj
                    })
                        
            except HttpError as e:
                # Skip if this object type has no resources or error
                if e.resp.status != 404:
                    print(f"Warning: Error listing {obj_type} objects: {e}")
                continue
            except Exception as e:
                print(f"Error listing {obj_type} objects: {e}")
                continue
        
        return matching_objects

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
            raise GoogleWalletAPIError(
                f"Error creating pass object: {e}",
                status_code=e.resp.status if hasattr(e, 'resp') else None,
            ) from e
    
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
            # Google Wallet "GenericClass" has a restricted schema. Many fields commonly used
            # in our local `class_json` (issuerName, header, cardTitle, logo, heroImage,
            # hexBackgroundColor, reviewStatus) are either object-level or not supported and
            # will be silently dropped by Google. To avoid confusion and accidental wipes,
            # only patch GenericClass with the subset we actually expect to persist.
            if class_type == "Generic" and isinstance(class_data, dict):
                allowed_generic_keys = {
                    "id",
                    "textModulesData",
                    "linksModuleData",
                    "imageModulesData",
                    "classTemplateInfo",
                    "messages",
                    "multipleDevicesAndHoldersAllowedStatus",
                    "viewUnlockRequirement",
                    "callbackOptions",
                    "securityAnimation",
                    "enableSmartTap",
                    "redemptionIssuers",
                    "merchantLocations",
                    "valueAddedModuleData",
                    "appLinkData",
                }
                class_data = {k: v for k, v in class_data.items() if k in allowed_generic_keys}

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
                    # Google Wallet does not allow patching reviewStatus. Remove it at any depth.
                    import copy
                    patch_body = copy.deepcopy(class_data)
                    def remove_review_status(obj):
                        if isinstance(obj, dict):
                            obj.pop('reviewStatus', None)
                            for value in obj.values():
                                remove_review_status(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                remove_review_status(item)
                    remove_review_status(patch_body)

                    # Use patch instead of update for partial updates (more forgiving)
                    print(f"Class exists, attempting to patch update...")
                    return resource.patch(
                        resourceId=class_data['id'],
                        body=patch_body
                    ).execute()
                except HttpError as update_error:
                    # Print detailed error for debugging
                    import json
                    print(f"Error updating class. Class data being sent:")
                    print(json.dumps(class_data, indent=2))
                    error_details = update_error.content.decode('utf-8') if hasattr(update_error, 'content') else str(update_error)
                    print(f"Error details: {error_details}")
                    raise GoogleWalletAPIError(
                        f"Error updating existing class: {update_error}\n\nClass data: {json.dumps(class_data, indent=2)}",
                        status_code=update_error.resp.status if hasattr(update_error, 'resp') else None,
                        detail=error_details,
                    ) from update_error
            else:
                raise GoogleWalletAPIError(
                    f"Error creating pass class: {e}",
                    status_code=e.resp.status if hasattr(e, 'resp') else None,
                ) from e
    
    
    def generate_save_link(self, object_id, class_type="EventTicket", class_id=None):
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
        
        # Ensure proper prefix (Issuer ID must be present for the link to work)
        object_id = self._prepare_ids_to_try(object_id)[0]
        
        obj_payload = {"id": object_id}
        if class_id:
            class_id = self._prepare_ids_to_try(class_id)[0]
            obj_payload["classId"] = class_id

        # Create JWT claims
        claims = {
            "iss": self.credentials.service_account_email,
            "aud": "google",
            "origins": [],
            "typ": "savetowallet",
            "iat": int(datetime.utcnow().timestamp()),
            "payload": {
                payload_key: [obj_payload]
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
        Update an existing pass class in Google Wallet using an ATOMIC patch.
        
        This fetches the current state, merges the changes, and sends a single patch.
        
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

            # 1. Fetch CURRENT state from Google
            try:
                current_data = resource.get(resourceId=full_class_id).execute()
            except Exception as e:
                print(f"Warning: Could not fetch current class {full_class_id} before update: {e}")
                current_data = {}

            # 2. Merge data and clean reviewStatus (Google Wallet doesn't allow updating it)
            import copy
            final_body = copy.deepcopy(current_data)
            final_body.update(class_data)
            
            def remove_review_status(obj):
                if isinstance(obj, dict):
                    obj.pop('reviewStatus', None)
                    for value in obj.values():
                        remove_review_status(value)
                elif isinstance(obj, list):
                    for item in obj:
                        remove_review_status(item)
            
            remove_review_status(final_body)
            
            # 3. Use patch for partial updates
            return resource.patch(
                resourceId=full_class_id,
                body=final_body
            ).execute()
            
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            raise GoogleWalletAPIError(
                f"Error updating pass class '{class_id}': {error_details}",
                status_code=e.resp.status if hasattr(e, 'resp') else None,
                detail=error_details,
            ) from e
    
    def _build_notification_message(self, header="Pass Updated", body="Your pass has been updated."):
        """Build a unique notification message that triggers a push notification.
        
        Google Wallet only triggers push notifications for messages with:
        - A unique `id` (not a duplicate of a previous message)
        - `messageType: TEXT_AND_NOTIFY`
        - A `displayInterval` with start/end timestamps
        """
        import time as _time
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        return {
            "id": f"update_notif_{int(_time.time())}",
            "header": header,
            "body": body,
            "kind": "walletobjects#walletObjectMessage",
            "messageType": "TEXT_AND_NOTIFY",
            "displayInterval": {
                "start": {"date": (now - timedelta(minutes=1)).isoformat() + "Z"},
                "end": {"date": (now + timedelta(hours=1)).isoformat() + "Z"}
            }
        }
    
    def send_push_notification(self, full_object_id, resource, message_header="📱 Pass Updated", message_body="Your pass information has been updated."):
        """
        Trigger a push notification using the EXACT same approach as debug_notification.py.
        
        This is the proven pattern:
        1. Fetch current pass data FROM Google (to get existing messages)
        2. APPEND a new unique message to the existing messages list
        3. Change groupingId to force Android to re-evaluate
        4. Send ONE minimal patch
        """
        import time as _time
        import uuid
        from datetime import datetime, timedelta
        
        try:
            # 1. Get current state from Google
            current_data = resource.get(resourceId=full_object_id).execute()
            
            # 2. Build unique notification message
            now = datetime.utcnow()
            message_id = f"update_notif_{int(_time.time())}"
            new_message = {
                "header": message_header,
                "body": message_body,
                "kind": "walletobjects#walletObjectMessage",
                "id": message_id,
                "messageType": "TEXT_AND_NOTIFY",
                "displayInterval": {
                    "start": {"date": (now - timedelta(minutes=1)).isoformat() + "Z"},
                    "end": {"date": (now + timedelta(hours=1)).isoformat() + "Z"}
                }
            }
            
            # 3. APPEND to existing messages (key difference from our old approach!)
            existing_messages = current_data.get("messages", [])
            existing_messages.append(new_message)
            
            # 4. Build minimal patch body (exactly like debug_notification.py)
            patch_body = {
                "state": "ACTIVE",
                "groupingId": f"group_{int(_time.time())}",
                "messages": existing_messages
            }
            
            # 5. Send single minimal patch
            resource.patch(resourceId=full_object_id, body=patch_body).execute()
            print(f"NOTIFICATION: Push notification sent for {full_object_id}")
            
        except Exception as e:
            print(f"NOTIFICATION WARNING: Failed to send push notification for {full_object_id}: {e}")
            # Don't raise - notification failure shouldn't block the data update
    
    def send_notification_only(self, object_id, class_type, message_header, message_body):
        """
        Send a push notification to a pass holder with ONLY a message append.
        
        Unlike send_push_notification, this does NOT change groupingId or state,
        which avoids triggering duplicate "data changed" notifications from Google.
        It only appends a TEXT_AND_NOTIFY message to the existing messages list.
        
        Args:
            object_id: Pass object ID (with or without issuer prefix)
            class_type: Type of pass (EventTicket, LoyaltyCard, Generic, etc.)
            message_header: Notification header text
            message_body: Notification body text
        """
        import time as _time
        from datetime import datetime, timedelta
        
        full_object_id = self._prepare_ids_to_try(object_id)[0]
        
        # Resolve the correct Google Wallet resource
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
        
        try:
            # 1. Fetch current pass to get existing messages
            current_data = resource.get(resourceId=full_object_id).execute()
            
            # 2. Build the notification message
            now = datetime.utcnow()
            new_message = {
                "header": message_header,
                "body": message_body,
                "kind": "walletobjects#walletObjectMessage",
                "id": f"notif_{int(_time.time())}",
                "messageType": "TEXT_AND_NOTIFY",
                "displayInterval": {
                    "start": {"date": (now - timedelta(minutes=1)).isoformat() + "Z"},
                    "end": {"date": (now + timedelta(hours=1)).isoformat() + "Z"}
                }
            }
            
            # 3. Append to existing messages
            existing_messages = current_data.get("messages", [])
            existing_messages.append(new_message)
            
            # 4. Build robust patch body (including state and groupingId to force immediate sync)
            patch_body = {
                "state": "ACTIVE",
                "groupingId": f"group_{int(_time.time())}",
                "messages": existing_messages
            }
            
            resource.patch(resourceId=full_object_id, body=patch_body).execute()
            print(f"NOTIFICATION: Custom notification sent for {full_object_id}")
            
        except Exception as e:
            print(f"NOTIFICATION WARNING: Failed to send notification for {full_object_id}: {e}")
    
    def update_pass_object(self, object_id, class_id, holder_name, holder_email, pass_data, class_type="EventTicket", status=None, notification_message=None):
        """
        Update an individual pass object in Google Wallet using an ATOMIC patch.
        
        This combines data updates and push notifications into ONE request, which
        is significantly faster and more reliable on Android devices.
        
        Args:
            object_id: Full object ID (with issuer prefix)
            class_id: Reference class ID (with issuer prefix)
            holder_name: Name of the pass holder
            holder_email: Email of the pass holder
            pass_data: Dictionary with pass-specific data (custom fields)
            class_type: Type of pass (EventTicket, LoyaltyCard, Generic)
            status: Optional pass status
            notification_message: Optional custom notification body message
            
        Returns:
            Updated object from Google Wallet API
        """
        import time as _time
        from datetime import datetime, timedelta

        try:
            # Ensure IDs have issuer prefix
            full_object_id = self._prepare_ids_to_try(object_id)[0]
            full_class_id = self._prepare_ids_to_try(class_id)[0]

            # 1. Select appropriate resource
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

            # 2. Fetch CURRENT state from Google
            try:
                current_data = resource.get(resourceId=full_object_id).execute()
                existing_messages = current_data.get("messages", [])
            except Exception as e:
                print(f"Warning: Could not fetch current object {full_object_id} before update: {e}")
                existing_messages = []

            # 3. Build the NEW pass data using appropriate builder
            if class_type == "EventTicket":
                object_data = self.build_event_ticket_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data, status=status, message_type=None
                )
            elif class_type == "LoyaltyCard":
                object_data = self.build_loyalty_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data, status=status, message_type=None
                )
            elif class_type == "GiftCard":
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data, status=status, message_type=None
                )
            elif class_type == "TransitPass":
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data, status=status, message_type=None
                )
            else:  # Generic
                object_data = self.build_generic_object(
                    full_object_id, full_class_id, holder_name, holder_email, pass_data, status=status, message_type=None
                )

            # 4. ATOMIC TRICK: Always append a Notification Message and rotate groupingId
            # This ensures that EVERY update triggers a visible push notification on Android.
            
            # Use default message if none provided
            msg_body = notification_message if notification_message else "Your pass information has been updated."
            
            now = datetime.utcnow()
            msg_id = f"notif_{int(_time.time())}"
            # If user explicitly provided messages, use their messageType for the push message too.
            push_message_type = "TEXT_AND_NOTIFY"
            user_messages = pass_data.get("messages") if isinstance(pass_data, dict) else None
            if isinstance(user_messages, list) and user_messages:
                last_type = user_messages[-1].get("messageType") or user_messages[-1].get("message_type")
                if isinstance(last_type, str) and last_type.strip():
                    push_message_type = last_type.strip()
            new_msg = {
                "header": "Mertesacker Home Office",
                "body": msg_body,
                "kind": "walletobjects#walletObjectMessage",
                "id": msg_id,
                "messageType": push_message_type,
                "displayInterval": {
                    "start": {"date": (now - timedelta(minutes=1)).isoformat() + "Z"},
                    "end": {"date": (now + timedelta(hours=24)).isoformat() + "Z"}
                }
            }
            # If Generic pass_data includes user-managed messages, prefer those over existing history.
            managed_messages_present = isinstance(user_messages, list) and user_messages and class_type == "Generic"
            if managed_messages_present:
                managed_messages = object_data.get("messages") or []
                object_data["messages"] = managed_messages + [new_msg]
            else:
                # Merge with existing messages (keep history but add new one)
                object_data["messages"] = existing_messages + [new_msg]
            
            # ANDROID UI TRICK: Force immediate refresh by changing groupingId
            # This is critical to make the notification pop up immediately
            object_data["groupingId"] = f"grp_{int(_time.time())}"

            # 5. EXECUTE SINGLE PATCH (Atomic operation)
            result = resource.patch(
                resourceId=full_object_id,
                body=object_data
            ).execute()
            
            print(f"SUCCESS: Atomic update/notification complete for {full_object_id}")
            return result
            
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            raise GoogleWalletAPIError(
                f"Error updating pass object '{object_id}': {error_details}",
                status_code=e.resp.status if hasattr(e, 'resp') else None,
                detail=error_details,
            ) from e
    
    def build_event_ticket_object(self, object_id, class_id, holder_name, holder_email, pass_data, custom_color=None, message_type="TEXT_AND_NOTIFY", status=None):
        """
        Build an EventTicket object structure for Google Wallet
        
        Args:
            object_id: Unique object ID
            class_id: Reference to class
            holder_name: Holder's name
            holder_email: Holder's email
            pass_data: Dictionary with pass-specific data (seat, gate, etc.)
            custom_color: Optional hex color to override class color (e.g., "#FF5722")
            message_type: Message type for notifications (TEXT or TEXT_AND_NOTIFY)
            
        Returns:
            Dictionary formatted for Google Wallet API
        """
        # Check for explicit custom values from pass_data (from UI) early
        pd = pass_data or {}
        custom_ticket_holder = pd.get("ticketHolderName") or pd.get("ticket_holder_name") or holder_name
        custom_conf_code = pd.get("confirmationCode") or pd.get("confirmation_code") or (object_id.split('.')[-1] if '.' in object_id else object_id)

        # Map local status to Google Wallet state
        gw_state = "ACTIVE"
        if status:
            s_upper = status.upper()
            if s_upper in ["ACTIVE", "COMPLETED", "EXPIRED", "INACTIVE"]:
                gw_state = s_upper

        obj = {
            "id": object_id,
            "classId": class_id,
            "state": gw_state,
            "ticketHolderName": custom_ticket_holder,
            "reservationInfo": {
                "confirmationCode": custom_conf_code
            }
        }

        # Add Branding (Logo/Hero) if in pass_data
        branding_logo_url = pd.get("logo_url") or pd.get("logoUrl")
        branding_hero_url = pd.get("hero_image_url") or pd.get("heroImageUrl") or pd.get("hero_url")
        if branding_logo_url:
            obj["logo"] = {
                "sourceUri": {"uri": str(branding_logo_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Logo"}}
            }
        if branding_hero_url:
            obj["heroImage"] = {
                "sourceUri": {"uri": str(branding_hero_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Hero Image"}}
            }
        
        # Add custom background color if provided
        if custom_color:
            obj["hexBackgroundColor"] = custom_color
        
        # Add message with specified messageType
        if message_type:
            obj["messages"] = [{
                "header": "Welcome",
                "body": "Your pass has been created",
                "messageType": message_type
            }]
        
        # Add seat information if available
        if pass_data:
            seat_value = pass_data.get("seatNumber") or pass_data.get("seat_number") or pass_data.get("seat", "")
            if seat_value:
                obj["seatInfo"] = {
                    "seat": {
                        "kind": "walletobjects#localizedString",
                        "defaultValue": {
                            "kind": "walletobjects#translatedString",
                            "language": "en-US",
                            "value": str(seat_value)
                        }
                    }
                }
            if "gate" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["gate"] = {
                    "kind": "walletobjects#localizedString",
                    "defaultValue": {
                        "kind": "walletobjects#translatedString",
                        "language": "en-US",
                        "value": str(pass_data["gate"])
                    }
                }
            if "row" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["row"] = {
                    "kind": "walletobjects#localizedString",
                    "defaultValue": {
                        "kind": "walletobjects#translatedString",
                        "language": "en-US",
                        "value": str(pass_data["row"])
                    }
                }
            if "section" in pass_data:
                obj["seatInfo"] = obj.get("seatInfo", {})
                obj["seatInfo"]["section"] = {
                    "kind": "walletobjects#localizedString",
                    "defaultValue": {
                        "kind": "walletobjects#translatedString",
                        "language": "en-US",
                        "value": str(pass_data["section"])
                    }
                }
            
            # Note: event_name and event_date come from the class definition, not the object
            # These should not be added here to avoid duplication
            
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
            
            # Add text modules if provided
            raw_modules = pass_data.get("textModulesData") or pass_data.get("text_modules", [])
            if raw_modules:
                obj["textModulesData"] = raw_modules
            
            if info_label_values:
                obj["infoModulesData"] = [{
                    "showTime": {},
                    "labelValueRows": [{
                        "columns": info_label_values
                    }]
                }]
        
        return obj
    
    def build_loyalty_object(self, object_id, class_id, holder_name, holder_email, pass_data, custom_color=None, message_type="TEXT_AND_NOTIFY", status=None):
        # Map local status to Google Wallet state
        gw_state = "ACTIVE"
        if status:
            s_upper = status.upper()
            if s_upper in ["ACTIVE", "COMPLETED", "EXPIRED", "INACTIVE"]:
                gw_state = s_upper
                
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": gw_state,
            "accountName": holder_name,
            "accountId": holder_email
        }
        
        if custom_color:
            obj["hexBackgroundColor"] = custom_color
        
        # Add message with specified messageType
        if message_type:
            obj["messages"] = [{
                "header": "Welcome",
                "body": "Your loyalty card has been created",
                "messageType": message_type
            }]
        
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
            
            # Combine with any other text modules from pass_data
            raw_modules = text_modules + (pass_data.get("textModulesData") or pass_data.get("text_modules", []))
            
            # Keep all text modules in textModulesData
            if raw_modules:
                obj["textModulesData"] = raw_modules
            
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
    
    def build_generic_object(self, object_id, class_id, holder_name, holder_email, pass_data, custom_color=None, message_type="TEXT_AND_NOTIFY", status=None):
        # Extract explicit generic fields sent by UI
        pd = pass_data or {}
        card_title = pd.get("card_title")
        header_text = pd.get("header_value")
        subheader_text = pd.get("subheader_value")

        # Generic *object*-level branding (Google ignores these on GenericClass)
        branding_logo_url = pd.get("logo_url") or pd.get("logoUrl")
        branding_hero_url = pd.get("hero_image_url") or pd.get("heroImageUrl") or pd.get("hero_url")
        branding_bg = custom_color or pd.get("hexBackgroundColor") or pd.get("hex_background_color") or pd.get("background_color") or pd.get("base_color")
        branding_bg = branding_bg if isinstance(branding_bg, str) and branding_bg.strip() else None
        
        # Map local status to Google Wallet state
        gw_state = "ACTIVE"
        if status:
            s_upper = status.upper()
            if s_upper in ["ACTIVE", "COMPLETED", "EXPIRED", "INACTIVE"]:
                gw_state = s_upper
                
        obj = {
            "id": object_id,
            "classId": class_id,
            "state": gw_state,
        }

        # header_text → Google "header"
        if isinstance(header_text, str) and header_text.strip():
            obj["header"] = {
                "defaultValue": {
                    "language": "en-US",
                    "value": header_text
                }
            }

        # card_title → Google "cardTitle" (large text on card)
        if isinstance(card_title, str) and card_title.strip():
            obj["cardTitle"] = {
                "defaultValue": {
                    "language": "en-US",
                    "value": card_title
                }
            }
        
        # subheader_value → Google "subheader"
        if isinstance(subheader_text, str) and subheader_text.strip():
            obj["subheader"] = {
                "defaultValue": {
                    "language": "en-US",
                    "value": subheader_text
                }
            }
        
        # Add custom background color if provided
        if branding_bg:
            obj["hexBackgroundColor"] = branding_bg

        if branding_logo_url:
            obj["logo"] = {
                "sourceUri": {"uri": str(branding_logo_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Logo"}}
            }
        if branding_hero_url:
            obj["heroImage"] = {
                "sourceUri": {"uri": str(branding_hero_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Hero Image"}}
            }
        
        # Barcode support (minimal: type + value)
        barcode_obj = None
        if isinstance(pd.get("barcode"), dict):
            barcode_obj = pd.get("barcode")
        else:
            bc_type = pd.get("barcode_type") or pd.get("barcodeType")
            bc_value = pd.get("barcode_value") or pd.get("barcodeValue")
            if (isinstance(bc_type, str) and bc_type.strip()) or (isinstance(bc_value, str) and bc_value.strip()):
                barcode_obj = {
                    "type": bc_type if bc_type else "QR_CODE",
                    "value": bc_value if bc_value else "",
                }
        if isinstance(barcode_obj, dict) and isinstance(barcode_obj.get("value"), str) and barcode_obj["value"].strip():
            obj["barcode"] = barcode_obj

        # Messages support
        user_messages = pd.get("messages")
        if isinstance(user_messages, list) and user_messages:
            def _map_user_message(m):
                if not isinstance(m, dict):
                    return None
                msg_type = m.get("messageType") or m.get("message_type") or "TEXT_AND_NOTIFY"
                msg_obj = {
                    "header": m.get("header") or "",
                    "body": m.get("body") or "",
                    "messageType": msg_type,
                }
                if m.get("id"):
                    msg_obj["id"] = m.get("id")
                return msg_obj
            mapped = [x for x in (_map_user_message(m) for m in user_messages) if x]
            if mapped:
                obj["messages"] = mapped
        elif message_type:
            obj["messages"] = [{
                "header": "Welcome",
                "body": "Your pass has been created",
                "messageType": message_type
            }]
        
        if pass_data:
            
            # Gather all text modules and keep them ALL in textModulesData.
            # The front/back split is controlled by classTemplateInfo on the CLASS,
            # not by removing items from the object.
            all_raw_modules = (pass_data.get("textModulesData") or pass_data.get("text_modules", [])).copy()
            if "description" in pass_data and pass_data["description"]:
                all_raw_modules.append({
                    "header": "Description",
                    "body": str(pass_data["description"]),
                    "id": "description"
                })
            
            if all_raw_modules:
                obj["textModulesData"] = all_raw_modules
            
            # Add info modules for all other data
            info_label_values = []
            
            # Skip fields already used in header, cardTitle, subheader, or textModules
            skip_fields = [
                "header_value",
                "subheader",
                "subheader_value",
                "description",
                "textModulesData",
                "messages",
                "messageType",
                "message_header",
                "message_body",
                "barcode",
                "barcode_type",
                "barcode_value",
                # Branding fields used above (should not appear as info rows)
                "logo_url",
                "logoUrl",
                "hero_image_url",
                "heroImageUrl",
                "hero_url",
                "hexBackgroundColor",
                "background_color",
                "base_color",
            ]
            
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