import json 
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Issuer ID
ISSUER_ID = "3388000000023033675"

SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']
KEY_FILE_PATH = 'service_account.json' # Default key file name

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
        # Correction: 'global' must be declared at the very beginning of the function
        global KEY_FILE_PATH
        
        # Check if the key file exists at the default path
        if not os.path.exists(KEY_FILE_PATH):
            # Try the alternative file name commonly used in your project
            if os.path.exists('wallet-pass-476608-e7bc0f55b858.json'):
                 KEY_FILE_PATH = 'wallet-pass-476608-e7bc0f55b858.json'
            else:
                raise FileNotFoundError(f"Credentials file not found: {KEY_FILE_PATH}")
            
        self.credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE_PATH, scopes=SCOPES)
        self.service = build('walletobjects', 'v1', credentials=self.credentials)

    def _prepare_ids_to_try(self, input_id):
        """
        Smart helper to prepare a list of potential Resource IDs.
        Automatically handles the Issuer ID prefix logic.
        """
        clean_id = input_id.strip()
        ids = []

        # 1. Ideal scenario: The input ID already starts with the Issuer ID
        if clean_id.startswith(ISSUER_ID):
            ids.append(clean_id)
        
        # 2. Common scenario: User entered only the Suffix (Name)
        else:
            # Priority 1: Try constructing the valid ID (Issuer.Suffix)
            ids.append(f"{ISSUER_ID}.{clean_id}")
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