"""
FastAPI Application for Wallet Passes
Provides RESTful API endpoints for managing pass classes and passes
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import copy
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path
import mysql.connector

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs
from database.db_manager import DatabaseManager
from api.models import (
    ClassCreate, ClassUpdate, ClassResponse,
    PassCreate, PassUpdate, PassStatusUpdate, PassResponse,
    HealthResponse, MessageResponse
)

# Import service layer and wallet client
from services.class_update_service import propagate_class_update_to_passes
from wallet_service import WalletClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize wallet client (will be used for class updates)
try:
    wallet_client = WalletClient()
    logger.info("WalletClient initialized successfully")
except Exception as e:
    wallet_client = None
    logger.warning(f"WalletClient initialization failed: {e}. Google Wallet sync will be disabled.")

def get_db_connection():
    return mysql.connector.connect(
        host=configs.DB_HOST,
        port=configs.DB_PORT,
        user=configs.DB_USER,
        password=configs.DB_PASSWORD,
        database=configs.DB_NAME
    )
# Initialize FastAPI app
app = FastAPI(
    title="Wallet Passes API",
    description="RESTful API for managing Google Wallet pass classes and passes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database manager
db = DatabaseManager()


# ========================================================================
# Health Check
# ========================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health status"""
    db_status = "disconnected"
    conn = None
    cursor = None

    try:
        # Attempt to establish a new database connection
        conn = get_db_connection() 
        cursor = conn.cursor()
        
        # Execute a simple query to verify connection
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        # If we reach here without errors, connection is successful
        db_status = "connected"
        
    except Exception as e:
        # Log any errors to the console
        print(f"⚠️ Health Check Failed: {e}")
        db_status = "disconnected"
        
    finally:
        # Always close cursor and connection if they were created
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except Exception as e:
            print(f"⚠️ Error closing connection: {e}")

    # Return the health status
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.now()
    )

# ========================================================================
# Classes Endpoints
# ========================================================================

@app.post("/classes/", response_model=MessageResponse, status_code=201, tags=["Classes"])
async def create_class(class_data: ClassCreate):
    """Create a new pass class"""
    try:
        # Extract relational fields from class_json if provided
        if class_data.class_json:
            from google_wallet_parser import parse_google_wallet_class
            parsed_metadata = parse_google_wallet_class(class_data.class_json)
            # Override any None values in class_data with parsed values
            if class_data.issuer_name is None: class_data.issuer_name = parsed_metadata.get('issuer_name')
            if class_data.base_color is None: class_data.base_color = parsed_metadata.get('base_color')
            if class_data.logo_url is None: class_data.logo_url = parsed_metadata.get('logo_url')
            if class_data.hero_image_url is None: class_data.hero_image_url = parsed_metadata.get('hero_image_url')
            if class_data.header_text is None: class_data.header_text = parsed_metadata.get('header_text')
            if class_data.card_title is None: class_data.card_title = parsed_metadata.get('card_title')
            if class_data.event_name is None: class_data.event_name = parsed_metadata.get('event_name')
            if class_data.venue_name is None: class_data.venue_name = parsed_metadata.get('venue_name')
            if class_data.venue_address is None: class_data.venue_address = parsed_metadata.get('venue_address')
            if class_data.event_start is None: class_data.event_start = parsed_metadata.get('event_start')
            if class_data.program_name is None: class_data.program_name = parsed_metadata.get('program_name')
            if class_data.transit_type is None: class_data.transit_type = parsed_metadata.get('transit_type')
            if class_data.transit_operator_name is None: class_data.transit_operator_name = parsed_metadata.get('transit_operator_name')

        success = db.create_class(
            class_id=class_data.class_id,
            class_type=class_data.class_type,
            issuer_name=class_data.issuer_name,
            base_color=class_data.base_color,
            logo_url=class_data.logo_url,
            hero_image_url=class_data.hero_image_url,
            header_text=class_data.header_text,
            card_title=class_data.card_title,
            event_name=class_data.event_name,
            venue_name=class_data.venue_name,
            venue_address=class_data.venue_address,
            event_start=class_data.event_start,
            program_name=class_data.program_name,
            transit_type=class_data.transit_type,
            transit_operator_name=class_data.transit_operator_name,
            class_json=class_data.class_json
        )
        
        if success:
            return MessageResponse(
                message=f"Class '{class_data.class_id}' created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create class")
            
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail=f"Class '{class_data.class_id}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/classes/", response_model=List[ClassResponse], tags=["Classes"])
async def get_all_classes():
    """Retrieve all pass classes"""
    try:
        classes = db.get_all_classes()
        return classes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/classes/{class_id}", response_model=ClassResponse, tags=["Classes"])
async def get_class(class_id: str):
    """Retrieve a specific pass class by ID"""
    try:
        class_data = db.get_class(class_id)
        
        if not class_data:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
        
        return class_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/classes/{class_id}", response_model=MessageResponse, tags=["Classes"])
async def update_class(class_id: str, class_data: ClassUpdate):
    """Update a pass class and propagate changes to all associated passes"""
    try:
        # Check if class exists
        existing_class = db.get_class(class_id)
        if not existing_class:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
        
        # Only update fields that are provided
        update_data = class_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Extract relational fields from class_json if provided
        if "class_json" in update_data and update_data["class_json"]:
            from google_wallet_parser import parse_google_wallet_class
            parsed_metadata = parse_google_wallet_class(update_data["class_json"])
            # Merge parsed metadata into update_data, avoiding overwriting explicit fields
            for key, value in parsed_metadata.items():
                if key not in update_data and value is not None:
                    update_data[key] = value

        # region agent log
        try:
            import json as _json, time as _time
            with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                _ts = int(_time.time() * 1000)
                _f.write(_json.dumps({
                    "id": f"log_{_ts}",
                    "timestamp": _ts,
                    "location": "api/api.py:update_class:before_db_update",
                    "message": "About to update class in DB",
                    "data": {"class_id": class_id, "update_keys": list(update_data.keys())},
                    "runId": "initial",
                    "hypothesisId": "H1"
                }) + "\n")
        except Exception:
            pass
        # endregion

        # Remove class_id from update_data to avoid 'multiple values' error
        if "class_id" in update_data:
            update_data.pop("class_id")

        # Step 1: Update local database
        success = db.update_class(class_id, **update_data)
        
        # Step 2: Get the updated class data for Google Wallet sync
        updated_class = db.get_class(class_id)
        
        # Step 3: Sync to Google Wallet and propagate to passes
        if wallet_client and updated_class.get('class_json'):
            try:
                # 3a: Upsert the class in Google Wallet (Creates if missing, Updates if exists)
                # This ensures we don't fail if the class was only local before
                logger.info(f"Syncing class '{class_id}' to Google Wallet")
                wallet_client.create_pass_class(
                    class_data=updated_class['class_json'],
                    class_type=updated_class.get('class_type', 'Generic')
                )

                # region agent log
                try:
                    import json as _json, time as _time
                    with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                        _ts = int(_time.time() * 1000)
                        _f.write(_json.dumps({
                            "id": f"log_{_ts}",
                            "timestamp": _ts,
                            "location": "api/api.py:update_class:before_propagate",
                            "message": "Calling propagate_class_update_to_passes",
                            "data": {"class_id": class_id},
                            "runId": "initial",
                            "hypothesisId": "H1"
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                
                # 3b: Propagate updates to all pass objects (triggers pass-level notifications)
                logger.info(f"Propagating class '{class_id}' updates to affected passes")
                propagation_result = propagate_class_update_to_passes(
                    class_id=class_id,
                    updated_class=updated_class,
                    db_manager=db,
                    wallet_client=wallet_client
                )

                # region agent log
                try:
                    import json as _json, time as _time
                    with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                        _ts = int(_time.time() * 1000)
                        _f.write(_json.dumps({
                            "id": f"log_{_ts}",
                            "timestamp": _ts,
                            "location": "api/api.py:update_class:after_propagate",
                            "message": "Finished propagate_class_update_to_passes",
                            "data": propagation_result,
                            "runId": "initial",
                            "hypothesisId": "H2"
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                
                # Build response message
                updated_count = propagation_result["updated_count"]
                failed_count = propagation_result["failed_count"]
                total_count = propagation_result["total_count"]
                
                if failed_count > 0:
                    # Partial success
                    message = (
                        f"✅ Class updated! "
                        f"📱 Notification sent to {updated_count}/{total_count} users. "
                        f"⚠️ {failed_count} failed."
                    )
                    logger.warning(f"Partial sync for class '{class_id}': {propagation_result['errors']}")
                else:
                    # Full success
                    message = (
                        f"✅ Class updated! "
                        f"📱 Notification sent to {updated_count} users."
                    )
                    logger.info(f"Successfully synced class '{class_id}' and {updated_count} passes")
                
                return MessageResponse(
                    message=message,
                    success=True
                )
                
            except Exception as e:
                # Google Wallet sync failed, but local DB update succeeded
                error_msg = str(e)
                logger.error(f"Google Wallet sync failed for class '{class_id}': {error_msg}")
                return MessageResponse(
                    message=f"Class updated locally. ⚠️ Google Wallet sync failed: {error_msg}",
                    success=True
                )
        else:
            # No Google Wallet sync needed/possible
            reason = "WalletClient not available" if not wallet_client else "No class_json found"
            logger.warning(f"Class '{class_id}' updated locally only. Reason: {reason}. Google Wallet sync is DISABLED.")
            return MessageResponse(
                message=f"Class '{class_id}' updated locally only (no wallet sync).",
                success=True
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating class '{class_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/classes/sync", response_model=MessageResponse, tags=["Classes"])
async def sync_classes_from_google():
    """
    Fetch all classes from Google Wallet and sync them to local database.
    Updates existing classes and creates new ones.
    """
    try:
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet client not initialized")
        
        # 1. Fetch all classes from Google Wallet
        logger.info("Fetching all classes from Google Wallet...")
        google_classes = wallet_client.list_all_classes()
        logger.info(f"Found {len(google_classes)} classes in Google Wallet")
        
        synced_count = 0
        new_count = 0
        updated_count = 0
        errors = []
        
        # Import parser
        from google_wallet_parser import parse_google_wallet_class
        
        # 2. Process each class
        for google_class in google_classes:
            try:
                # Parse metadata
                metadata = parse_google_wallet_class(google_class)
                class_id = metadata['class_id']
                
                # Check if class exists locally
                existing_class = db.get_class(class_id)
                
                # Filter out reviewStatus from the class JSON to prevent it from being saved
                # This ensures we don't overwrite local review status with "UNDER_REVIEW" from Google
                def remove_review_status(obj):
                    if isinstance(obj, dict):
                        obj.pop('reviewStatus', None)
                        for value in obj.values():
                            remove_review_status(value)
                    elif isinstance(obj, list):
                        for item in obj:
                            remove_review_status(item)
                
                import copy
                clean_google_class = copy.deepcopy(google_class)
                remove_review_status(clean_google_class)
                
                if existing_class:
                    # Update parameters
                    logger.info(f"Updating local class: {class_id}")
                    success = db.update_class(
                        class_id=class_id,
                        class_type=metadata['class_type'],
                        issuer_name=metadata.get('issuer_name'),
                        base_color=metadata.get('base_color'),
                        logo_url=metadata.get('logo_url'),
                        hero_image_url=metadata.get('hero_image_url'),
                        header_text=metadata.get('header_text'),
                        card_title=metadata.get('card_title'),
                        event_name=metadata.get('event_name'),
                        venue_name=metadata.get('venue_name'),
                        venue_address=metadata.get('venue_address'),
                        event_start=metadata.get('event_start'),
                        program_name=metadata.get('program_name'),
                        transit_type=metadata.get('transit_type'),
                        transit_operator_name=metadata.get('transit_operator_name'),
                    )
                    updated_count += 1
                else:
                    # Create new class
                    logger.info(f"Creating local class: {class_id}")
                    success = db.create_class(
                        class_id=class_id,
                        class_type=metadata['class_type'],
                        issuer_name=metadata.get('issuer_name'),
                        base_color=metadata.get('base_color'),
                        logo_url=metadata.get('logo_url'),
                        hero_image_url=metadata.get('hero_image_url'),
                        header_text=metadata.get('header_text'),
                        card_title=metadata.get('card_title'),
                        event_name=metadata.get('event_name'),
                        venue_name=metadata.get('venue_name'),
                        venue_address=metadata.get('venue_address'),
                        event_start=metadata.get('event_start'),
                        program_name=metadata.get('program_name'),
                        transit_type=metadata.get('transit_type'),
                        transit_operator_name=metadata.get('transit_operator_name'),
                    )
                    if success:
                        new_count += 1
                
                synced_count += 1
                
            except Exception as e:
                error_msg = f"Error syncing class {google_class.get('id')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        message = f"Sync complete. Processed {synced_count} classes (New: {new_count}, Updated: {updated_count})."
        
        return MessageResponse(
            message=message,
            success=True
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/classes/{class_id}", response_model=MessageResponse, tags=["Classes"])
async def delete_class(class_id: str):
    """Delete a pass class (will cascade delete associated passes)"""
    try:
        # Check if class exists
        existing_class = db.get_class(class_id)
        if not existing_class:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
        
        success = db.delete_class(class_id)
        
        if success:
            return MessageResponse(
                message=f"Class '{class_id}' deleted successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to delete class")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Passes Endpoints
# ========================================================================

@app.post("/passes/", response_model=MessageResponse, status_code=201, tags=["Passes"])
async def create_pass(pass_data: PassCreate):
    """Create a new pass"""
    try:
        # Verify class exists
        class_exists = db.get_class(pass_data.class_id)
        if not class_exists:
            raise HTTPException(status_code=404, detail=f"Class '{pass_data.class_id}' not found")
        
        success = db.create_pass(
            object_id=pass_data.object_id,
            class_id=pass_data.class_id,
            holder_name=pass_data.holder_name,
            holder_email=pass_data.holder_email,
            pass_data=pass_data.pass_data,
            status=pass_data.status.value
        )
        
        if success:
            return MessageResponse(
                message=f"Pass '{pass_data.object_id}' created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create pass")
            
    except HTTPException:
        raise
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail=f"Pass '{pass_data.object_id}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/passes/", response_model=List[PassResponse], tags=["Passes"])
async def get_passes(
    status: Optional[str] = Query(None, description="Filter by status: 'Active' or 'Expired'")
):
    """Retrieve all passes with optional status filter"""
    try:
        if status:
            if status == "Active":
                passes = db.get_active_passes()
            elif status == "Expired":
                passes = db.get_expired_passes()
            else:
                raise HTTPException(status_code=400, detail="Status must be 'Active' or 'Expired'")
        else:
            passes = db.get_all_passes()
        
        return passes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/passes/google/class/{class_id}", tags=["Passes"])
async def get_passes_from_google_by_class(class_id: str):
    """
    Fetch all pass objects for a class **live from Google Wallet API**.
    No local database is involved in the read.
    """
    if not wallet_client:
        raise HTTPException(status_code=503, detail="Google Wallet service not initialized")
    try:
        raw_objects = wallet_client.list_class_objects(class_id)
        # list_class_objects returns [{'id':..., 'data':..., 'class_type':...}, ...]
        result = []
        for item in raw_objects:
            gw_obj = item.get("data", {})
            if not gw_obj:
                continue
            normalised = _normalize_google_pass(gw_obj)
            normalised["class_type"] = item.get("class_type", "Generic")
            result.append(normalised)
        return result
    except Exception as e:
        logger.error(f"Error fetching passes from Google Wallet for class '{class_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/passes/google/object/{object_id}", tags=["Passes"])
async def get_pass_from_google(object_id: str):
    """
    Fetch a single pass object **live from Google Wallet API**.
    Tries all object resource types (Generic, EventTicket, Loyalty, etc.).
    No local database is involved in the read.
    """
    if not wallet_client:
        raise HTTPException(status_code=503, detail="Google Wallet service not initialized")

    full_object_id = f"{configs.ISSUER_ID}.{object_id}" if not object_id.startswith(configs.ISSUER_ID) else object_id

    object_resources = [
        ("Generic",     wallet_client.service.genericobject()),
        ("EventTicket", wallet_client.service.eventticketobject()),
        ("LoyaltyCard", wallet_client.service.loyaltyobject()),
        ("GiftCard",    wallet_client.service.giftcardobject()),
        ("TransitPass", wallet_client.service.transitobject()),
    ]

    for class_type, resource in object_resources:
        try:
            gw_obj = resource.get(resourceId=full_object_id).execute()
            normalised = _normalize_google_pass(gw_obj)
            normalised["class_type"] = class_type
            return normalised
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found in Google Wallet")


@app.get("/passes/{object_id}", response_model=PassResponse, tags=["Passes"])
async def get_pass(object_id: str):
    """Retrieve a specific pass by object ID"""
    try:
        pass_data = db.get_pass(object_id)
        
        if not pass_data:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        return pass_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/passes/class/{class_id}", response_model=List[PassResponse], tags=["Passes"])
async def get_passes_by_class(class_id: str):
    """Get all passes for a specific class"""
    try:
        # Verify class exists
        class_exists = db.get_class(class_id)
        if not class_exists:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
        
        passes = db.get_passes_by_class(class_id)
        return passes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/passes/email/{email}", response_model=List[PassResponse], tags=["Passes"])
async def get_passes_by_email(email: str):
    """Get all passes for a specific user email"""
    try:
        passes = db.get_passes_by_email(email)
        return passes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/passes/{object_id}", response_model=MessageResponse, tags=["Passes"])
async def update_pass(object_id: str, pass_update: PassUpdate, sync_to_google: bool = True):
    """Update a pass and optionally sync to Google Wallet"""
    try:
        # Check if pass exists
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        # Build kwargs for db.update_pass
        db_kwargs = {}
        
        if pass_update.holder_name is not None:
            db_kwargs['holder_name'] = pass_update.holder_name
        if pass_update.holder_email is not None:
            db_kwargs['holder_email'] = pass_update.holder_email
        if pass_update.status is not None:
            db_kwargs['status'] = pass_update.status.value
        if pass_update.pass_data is not None:
            db_kwargs['pass_data'] = pass_update.pass_data
            
        logger.info(f"Updating pass '{object_id}' with db_kwargs keys: {list(db_kwargs.keys())}")
        if 'pass_data' in db_kwargs:
            logger.info(f"  pass_data keys: {list(db_kwargs['pass_data'].keys())}")
        
        if not db_kwargs:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        db_success = db.update_pass(object_id, **db_kwargs)
        
        # 2. Sync to Google Wallet if requested and client is available
        wallet_message = ""
        if sync_to_google:
            if wallet_client:
                try:
                    updated_pass = db.get_pass(object_id)
                    class_info = db.get_class(updated_pass['class_id'])
                
                    if class_info:
                        logger.info(f"Syncing pass '{object_id}' to Google Wallet")
                        wallet_client.update_pass_object(
                            object_id=object_id,
                            class_id=updated_pass['class_id'],
                            holder_name=updated_pass['holder_name'],
                            holder_email=updated_pass['holder_email'],
                            pass_data=updated_pass.get('pass_data', {}),
                            class_type=class_info.get('class_type', 'Generic')
                        )
                        wallet_message = " 📱 Synced to Google Wallet."
                    else:
                        wallet_message = " ⚠️ Could not sync to Google Wallet (Class info missing)."
                except Exception as e:
                    logger.error(f"Failed to sync updated pass to Google Wallet: {e}")
                    wallet_message = f" ⚠️ Google Wallet sync failed: {str(e)}"
            else:
                wallet_message = " ⚠️ Google Wallet sync disabled (Check server logs)."

        if db_success:
            return MessageResponse(
                message=f"Pass '{object_id}' updated successfully.{wallet_message}",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update pass locally")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_pass: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/passes/{object_id}/push", response_model=MessageResponse, tags=["Passes"])
async def push_pass_to_google(object_id: str):
    """Explicitly push the current local database state of a pass to Google Wallet"""
    try:
        # Check if pass exists
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
            
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet sync disabled (Check server logs).")
            
        class_info = db.get_class(existing_pass['class_id'])
        if not class_info:
            raise HTTPException(status_code=404, detail="Class info missing for this pass.")
            
        logger.info(f"Explicitly pushing pass '{object_id}' to Google Wallet")
        wallet_client.update_pass_object(
            object_id=object_id,
            class_id=existing_pass['class_id'],
            holder_name=existing_pass['holder_name'],
            holder_email=existing_pass['holder_email'],
            pass_data=existing_pass.get('pass_data', {}),
            class_type=class_info.get('class_type', 'Generic'),
            status=existing_pass.get('status')
        )
        
        return MessageResponse(
            message=f"📱 Pass '{object_id}' successfully synced to Google Wallet.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to push pass to Google Wallet: {e}")
        raise HTTPException(status_code=500, detail=f"Google Wallet push failed: {str(e)}")


@app.put("/passes/{object_id}/status", response_model=MessageResponse, tags=["Passes"])
async def update_pass_status(object_id: str, status_data: PassStatusUpdate):
    """Update only the status of a pass"""
    try:
        # Check if pass exists
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        success = db.update_pass_status(object_id, status_data.status.value)
        
        if success:
            return MessageResponse(
                message=f"Pass '{object_id}' status updated to '{status_data.status.value}'",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update pass status")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/passes/{object_id}", response_model=MessageResponse, tags=["Passes"])
async def delete_pass(object_id: str):
    """Delete a pass"""
    try:
        # Check if pass exists
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        success = db.delete_pass(object_id)
        
        if success:
            return MessageResponse(
                message=f"Pass '{object_id}' deleted successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to delete pass")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Root Endpoint
# ========================================================================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to Wallet Passes API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post("/passes/sync", response_model=MessageResponse, tags=["Passes"])
async def sync_passes():
    """Sync all pass objects from Google Wallet to local database"""
    try:
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet service not initialized")
            
        logger.info("Starting pass objects sync from Google Wallet")
        
        # 1. Fetch all pass objects from Google Wallet
        google_passes = wallet_client.list_all_pass_objects()
        
        synced_count = 0
        new_count = 0
        updated_count = 0
        errors = []
        
        # 2. Process each pass and save to local DB
        for google_pass in google_passes:
            try:
                # Extract full ID with issuer prefix
                full_object_id = google_pass.get('id')
                # Extract local ID (suffix) for database consistency if needed, 
                # but we usually store the full object_id in Passes_Table
                # UPDATE: User requested to strip issuer ID prefix from object_id
                if full_object_id and full_object_id.startswith(configs.ISSUER_ID + "."):
                    object_id = full_object_id.split(".", 1)[1]
                else:
                    object_id = full_object_id
                
                # Check if pass already exists locally
                existing_pass = db.get_pass(object_id)
                
                # Extract metadata
                class_id = google_pass.get('classId')
                # Remove issuer prefix from class_id for local DB storage if it matches our ISSUER_ID
                if class_id and class_id.startswith(configs.ISSUER_ID + "."):
                    local_class_id = class_id.split(".", 1)[1]
                else:
                    local_class_id = class_id
                
                # Extract holder info - this varies by object type
                holder_name = ""
                holder_email = ""
                
                # Try common fields for different pass types
                if 'ticketHolderName' in google_pass:
                    holder_name = google_pass['ticketHolderName']
                elif 'accountName' in google_pass:
                    holder_name = google_pass['accountName']
                elif 'passengerName' in google_pass:
                    holder_name = google_pass['passengerName']
                
                if 'accountId' in google_pass:
                    holder_email = google_pass['accountId']
                
                # If we still don't have email/name, try custom modules or just leave blank
                # In our system holder_email is UNIQUE and REQUIRED, this might be a problem for sync
                # if the user manually created passes in Google Wallet console without emails.
                if not holder_email:
                    holder_email = f"unknown_{object_id}@example.com"
                if not holder_name:
                    holder_name = "Unknown Holder"

                # Prepare pass_data (everything else as JSON)
                pass_data_cleaned = copy.deepcopy(google_pass)
                # Remove common fields that are already in separate columns
                pass_data_cleaned.pop('id', None)
                pass_data_cleaned.pop('classId', None)
                pass_data_cleaned.pop('ticketHolderName', None)
                pass_data_cleaned.pop('accountName', None)
                pass_data_cleaned.pop('accountId', None)
                pass_data_cleaned.pop('state', None)
                
                status = "Active" if google_pass.get('state') == "ACTIVE" else "Expired"
                
                if existing_pass:
                    # Update parameters
                    logger.info(f"Updating local pass: {object_id}")
                    db.update_pass(
                        object_id=object_id,
                        holder_name=holder_name,
                        holder_email=holder_email,
                        status=status,
                        pass_data=pass_data_cleaned
                    )
                    updated_count += 1
                else:
                    # Create new pass
                    logger.info(f"Creating local pass: {object_id}")
                    # Ensure class exists locally before creating pass (FK constraint)
                    if not db.get_class(local_class_id):
                        # Auto-create the missing class from Google Wallet
                        logger.warning(f"Class '{local_class_id}' not found locally. Auto-syncing from Google...")
                        try:
                            from google_wallet_parser import parse_google_wallet_class
                            # Fetch class data from Google
                            full_class_id = f"{configs.ISSUER_ID}.{local_class_id}"
                            google_class_data = wallet_client.get_class(full_class_id)
                            if google_class_data:
                                meta = parse_google_wallet_class(google_class_data)
                                db.create_class(
                                    class_id=local_class_id,
                                    class_type=meta['class_type'],
                                    issuer_name=meta.get('issuer_name'),
                                    base_color=meta.get('base_color'),
                                    logo_url=meta.get('logo_url'),
                                    hero_image_url=meta.get('hero_image_url'),
                                    header_text=meta.get('header_text'),
                                    card_title=meta.get('card_title'),
                                    event_name=meta.get('event_name'),
                                    venue_name=meta.get('venue_name'),
                                    venue_address=meta.get('venue_address'),
                                    event_start=meta.get('event_start'),
                                    program_name=meta.get('program_name'),
                                    transit_type=meta.get('transit_type'),
                                    transit_operator_name=meta.get('transit_operator_name'),
                                )
                                logger.info(f"Auto-created class '{local_class_id}'")
                            else:
                                logger.warning(f"Class '{local_class_id}' not found in Google Wallet either. Skipping pass.")
                                errors.append(f"Class '{local_class_id}' missing for pass '{object_id}'")
                                continue
                        except Exception as class_err:
                            logger.warning(f"Failed to auto-create class '{local_class_id}': {class_err}. Skipping pass.")
                            errors.append(f"Failed to create class '{local_class_id}': {class_err}")
                            continue
                         
                    db.create_pass(
                        object_id=object_id,
                        class_id=local_class_id,
                        holder_name=holder_name,
                        holder_email=holder_email,
                        status=status,
                        pass_data=pass_data_cleaned
                    )
                    new_count += 1
                
                synced_count += 1
                
            except Exception as e:
                error_msg = f"Error syncing pass {google_pass.get('id')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        message = f"Sync complete. Processed {synced_count} passes (New: {new_count}, Updated: {updated_count})."
        
        return MessageResponse(
            message=message,
            success=True
        )
            
    except Exception as e:
        logger.error(f"Pass sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Google Wallet Live Read Endpoints (no local DB write)
# ========================================================================

def _normalize_google_pass(gw_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw Google Wallet pass object into a normalised dict that
    matches the shape the Manage Passes UI expects.
    """
    full_object_id = gw_obj.get("id", "")
    # Strip issuer prefix  e.g. "3388000000022...<issuer>.ABC" → "ABC"
    if full_object_id.startswith(configs.ISSUER_ID + "."):
        object_id = full_object_id.split(".", 1)[1]
    else:
        object_id = full_object_id

    class_id_full = gw_obj.get("classId", "")
    if class_id_full.startswith(configs.ISSUER_ID + "."):
        local_class_id = class_id_full.split(".", 1)[1]
    else:
        local_class_id = class_id_full

    # Extract holder name from whichever field is present
    holder_name = (
        gw_obj.get("ticketHolderName")
        or gw_obj.get("accountName")
        or gw_obj.get("passengerName")
        or "Unknown Holder"
    )
    holder_email = gw_obj.get("accountId") or f"unknown_{object_id}@example.com"
    status = "Active" if gw_obj.get("state") == "ACTIVE" else "Expired"

    # Everything else goes into pass_data
    pass_data = copy.deepcopy(gw_obj)
    for key in ("id", "classId", "ticketHolderName", "accountName",
                "accountId", "passengerName", "state"):
        pass_data.pop(key, None)

    return {
        "object_id": object_id,
        "class_id": local_class_id,
        "holder_name": holder_name,
        "holder_email": holder_email,
        "status": status,
        "pass_data": pass_data,
        "created_at": None,
        "updated_at": None,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)

