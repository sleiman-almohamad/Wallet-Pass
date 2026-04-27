"""
FastAPI Application for Wallet Passes
Provides RESTful API endpoints for managing pass classes and passes
"""

from fastapi import FastAPI, HTTPException, Query, Request, Response, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import copy
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import sys
from pathlib import Path
import mysql.connector
from fastapi.templating import Jinja2Templates

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import configs
from database.db_manager import DatabaseManager
from api.models import (
    HealthResponse, MessageResponse, NotificationRequest, AppleRegistrationRequest,
    ClassCreate, ClassUpdate, ClassResponse,
    AppleTemplateCreate, AppleTemplateUpdate, AppleTemplateResponse,
    PassCreate, PassUpdate, PassResponse, PassStatusUpdate,
    ApplePassCreate, ApplePassUpdate, ApplePassResponse,
    QRCampaignCreate, QRCampaignUpdate, QRCampaignResponse
)

# Import service layer and wallet client
from services.class_update_service import propagate_class_update_to_passes
from services.google_wallet_service import WalletClient
from exceptions import (
    WalletPassError, DatabaseError, DuplicateRecordError,
    GoogleWalletError, ValidationError,
)
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

# Middleware to skip ngrok browser warning
@app.middleware("http")
async def add_ngrok_skip_warning_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Initialize database manager
db = DatabaseManager()

# Mount static directory for serving uploaded images
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup Jinja2 templates for landing pages
templates_path = Path(__file__).parent.parent / "templates"
templates_path.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))

# ========================================================================
# Caching Strategy
# ========================================================================
# slug -> (campaign_data, timestamp)
CAMPAIGN_CACHE: Dict[str, Any] = {}
CACHE_TTL = 300 # 5 minutes (300 seconds)

def get_cached_campaign(slug: str):
    import time
    now = time.time()
    if slug in CAMPAIGN_CACHE:
        data, ts = CAMPAIGN_CACHE[slug]
        if now - ts < CACHE_TTL:
            return data
    
    # Not in cache or expired
    campaign = db.get_campaign(slug)
    if campaign:
        CAMPAIGN_CACHE[slug] = (campaign, now)
    return campaign

def invalidate_campaign_cache(slug: str = None):
    if slug:
        CAMPAIGN_CACHE.pop(slug, None)
    else:
        CAMPAIGN_CACHE.clear()


# ========================================================================
# Image Upload
# ========================================================================

@app.post("/upload/image", tags=["Storage"])
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload an image and return its public URL"""
    try:
        # Create unique filename with URL-safe characters
        import time
        import os
        import re
        
        # Strip extension and sanitize base name
        base_name, ext = os.path.splitext(file.filename)
        safe_base = re.sub(r'[^a-zA-Z0-9_-]', '', base_name.replace(' ', '_'))
        filename = f"img_{int(time.time())}_{safe_base}{ext}"
        
        file_path = static_dir / "images" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Construct public URL
        # We prioritize PUBLIC_URL from configs to ensure Google Wallet can reach the images
        base_url = configs.PUBLIC_URL if hasattr(configs, "PUBLIC_URL") and configs.PUBLIC_URL else str(request.base_url).rstrip("/")
        public_url = f"{base_url.rstrip('/')}/static/images/{filename}"
        
        return {
            "url": public_url,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



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
            from core.google_wallet_parser import parse_google_wallet_class
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
            header=class_data.header,
            subheader=class_data.subheader,
            card_title=class_data.card_title,
            event_name=class_data.event_name,
            venue_name=class_data.venue_name,
            venue_address=class_data.venue_address,
            event_start=class_data.event_start,
            program_name=class_data.program_name,
            transit_type=class_data.transit_type,
            transit_operator_name=class_data.transit_operator_name,
            text_module_rows=class_data.text_module_rows,
            class_json=class_data.class_json
        )
        
        if success:
            # Re-fetch from DB to get the final synthesized class_json
            newly_created_class = db.get_class(class_data.class_id)
            
            if wallet_client and newly_created_class and newly_created_class.get('class_json'):
                try:
                    logger.info(f"Syncing new class '{class_data.class_id}' to Google Wallet")
                    wallet_client.create_pass_class(
                        class_data=newly_created_class['class_json'],
                        class_type=newly_created_class.get('class_type', 'Generic')
                    )
                except Exception as e:
                    logger.error(f"Google Wallet sync failed for new class '{class_data.class_id}': {e}")
                    return MessageResponse(
                        message=f"Class created locally. ⚠️ Google Wallet sync failed: {str(e)}",
                        success=True
                    )
            
            return MessageResponse(
                message=f"Class '{class_data.class_id}' created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create class")
            
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=f"Class '{class_data.class_id}' already exists")
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except WalletPassError as e:
        raise HTTPException(status_code=500, detail=str(e))
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
async def update_class(class_id: str, class_data: ClassUpdate, sync_to_google: bool = True, notification_message: Optional[str] = None):
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
            from core.google_wallet_parser import parse_google_wallet_class
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
        
        # Step 2: If sync_to_google is False, just return local success
        if not sync_to_google:
            return MessageResponse(
                message=f"✅ Template '{class_id}' saved to local database.",
                success=True
            )
        
        # Step 3: Get the updated class data for Google Wallet sync
        updated_class = db.get_class(class_id)
        
        # Step 4: Sync to Google Wallet and propagate to passes
        if wallet_client and updated_class.get('class_json'):
            try:
                # Only sync the class to Google Wallet when there's no custom notification message.
                # Patching the class triggers an automatic Google notification to all pass holders,
                # which would cause a duplicate if we also send an explicit message notification.
                if not notification_message:
                    logger.info(f"Syncing class '{class_id}' to Google Wallet")
                    # For Generic classes, Google only persists a limited schema. We still call
                    # create_pass_class(), but it will internally restrict the payload so the
                    # user doesn't expect branding fields to appear on the class response.
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
                    wallet_client=wallet_client,
                    notification_message=notification_message
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
    except GoogleWalletError as e:
        logger.error(f"Google Wallet error updating class '{class_id}': {str(e)}")
        raise HTTPException(status_code=502, detail=f"Google Wallet error: {str(e)}")
    except WalletPassError as e:
        logger.error(f"Error updating class '{class_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating class '{class_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/classes/sync", response_model=MessageResponse, tags=["Classes"])
async def sync_classes_from_google():
    """
    Fetch all classes from Google Wallet and sync them to local database.
    Updates existing classes and creates new ones.
    """
    try:
        if not configs.ALLOW_GOOGLE_CLASS_SYNC:
            raise HTTPException(
                status_code=403,
                detail="Syncing classes FROM Google is disabled (local DB is source of truth). "
                       "Set ALLOW_GOOGLE_CLASS_SYNC=true to enable."
            )
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
        from core.google_wallet_parser import parse_google_wallet_class
        
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
                    # IMPORTANT: never overwrite local fields with None during sync.
                    # Google may omit fields (especially for GenericClass branding),
                    # so we only apply non-None updates. text_module_rows is always applied.
                    update_kwargs = {
                        "class_type": metadata.get("class_type"),
                        "issuer_name": metadata.get("issuer_name"),
                        "base_color": metadata.get("base_color"),
                        "logo_url": metadata.get("logo_url"),
                        "hero_image_url": metadata.get("hero_image_url"),
                        "header_text": metadata.get("header_text"),
                        "card_title": metadata.get("card_title"),
                        "event_name": metadata.get("event_name"),
                        "venue_name": metadata.get("venue_name"),
                        "venue_address": metadata.get("venue_address"),
                        "event_start": metadata.get("event_start"),
                        "program_name": metadata.get("program_name"),
                        "transit_type": metadata.get("transit_type"),
                        "transit_operator_name": metadata.get("transit_operator_name"),
                    }
                    update_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}
                    update_kwargs["text_module_rows"] = metadata.get("text_module_rows", [])

                    success = db.update_class(class_id, **update_kwargs)
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
                        text_module_rows=metadata.get('text_module_rows', []),
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
# Apple Template Endpoints
# ========================================================================

@app.post("/templates/apple/", response_model=MessageResponse, status_code=201, tags=["Apple Templates"])
async def create_apple_template(template_data: AppleTemplateCreate):
    """Create a new Apple Wallet template"""
    try:
        success = db.create_apple_template(
            template_id=template_data.template_id,
            template_name=template_data.template_name,
            pass_style=template_data.pass_style,
            pass_type_identifier=template_data.pass_type_identifier,
            team_identifier=template_data.team_identifier
        )
        if success:
            return MessageResponse(
                message=f"Apple Template '{template_data.template_id}' created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create Apple template")
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail=f"Template '{template_data.template_id}' already exists")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/apple/", response_model=List[AppleTemplateResponse], tags=["Apple Templates"])
async def get_all_apple_templates():
    """Retrieve all Apple Wallet templates"""
    try:
        templates = db.get_all_apple_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/apple/{template_id}", response_model=AppleTemplateResponse, tags=["Apple Templates"])
async def get_apple_template(template_id: str):
    """Retrieve a specific Apple Wallet template by ID"""
    try:
        template = db.get_apple_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/templates/apple/{template_id}", response_model=MessageResponse, tags=["Apple Templates"])
async def update_apple_template(template_id: str, template_data: AppleTemplateUpdate):
    """Update an Apple Wallet template"""
    try:
        update_data = template_data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = db.update_apple_template(template_id, **update_data)
        if success:
            # Trigger push for all passes using this template
            try:
                from services.apple_wallet_service import AppleWalletService
                apple_service = AppleWalletService()
                apple_service.send_apple_template_notification(template_id, "Template Updated")
                logger.info(f"APPLE: Auto-pushed updates for all passes in template {template_id}")
            except Exception as e:
                logger.error(f"APPLE: Failed to auto-push template updates: {e}")
            return MessageResponse(
                message=f"Apple Template '{template_id}' updated successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/templates/apple/{template_id}", response_model=MessageResponse, tags=["Apple Templates"])
async def delete_apple_template(template_id: str):
    """Delete an Apple Wallet template"""
    try:
        success = db.delete_apple_template(template_id)
        if success:
            return MessageResponse(
                message=f"Apple Template '{template_id}' deleted successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Apple Pass Endpoints
# ========================================================================

@app.get("/passes/apple/", response_model=List[ApplePassResponse], tags=["Passes"])
async def get_all_apple_passes():
    """Retrieve all Apple Wallet passes"""
    try:
        passes = db.get_all_apple_passes()
        return passes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passes/apple/{serial_number}", response_model=ApplePassResponse, tags=["Passes"])
async def get_apple_pass(serial_number: str):
    """Retrieve a specific Apple Wallet pass by serial number"""
    try:
        pass_data = db.get_apple_pass(serial_number)
        if not pass_data:
            raise HTTPException(status_code=404, detail=f"Apple Pass '{serial_number}' not found")
        return pass_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/passes/apple/{serial_number}", response_model=MessageResponse, tags=["Passes"])
async def update_apple_pass(serial_number: str, pass_data: ApplePassUpdate):
    """Update an Apple Wallet pass, regenerate .pkpass, and push to device."""
    try:
        update_dict = pass_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        # Step A: Update database
        success = db.update_apple_pass(serial_number, **update_dict)
        if not success:
            raise HTTPException(status_code=404, detail=f"Apple Pass '{serial_number}' not found")

        # Step B: Regenerate the .pkpass file
        try:
            from services.apple_wallet_service import AppleWalletService
            apple_service = AppleWalletService()
            
            # Fetch fresh pass data (with updates applied)
            updated_pass = db.get_apple_pass(serial_number)
            template_id = updated_pass.get("template_id", "")
            template_data = db.get_apple_template(template_id)
            
            class_data = {
                "class_type": "Generic",
                "template_id": template_id,
                "pass_style": template_data.get("pass_style", "eventTicket") if template_data else "eventTicket",
            }
            
            apple_service.create_pass(
                class_data=class_data,
                pass_data=updated_pass,
                object_id=serial_number,
            )
            print(f"🔄 [UPDATE] Regenerated .pkpass for {serial_number}")
            
            # Step C: Send APNs push
            result = apple_service.send_push_notification(serial_number)
            logger.info(f"APPLE: Auto-pushed update for pass {serial_number}: {result}")
        except Exception as e:
            logger.error(f"APPLE: Failed to regenerate/push pass {serial_number}: {e}")
            import traceback; traceback.print_exc()

        return MessageResponse(
            message=f"Apple Pass '{serial_number}' updated, regenerated, and push sent.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passes/apple/{serial_number}/download", tags=["Passes"])
async def download_apple_pass(serial_number: str):
    """Generate and download an Apple Wallet pass with iOS compatible MIME types"""
    from fastapi.responses import FileResponse
    import os
    try:
        pass_data = db.get_apple_pass(serial_number)
        if not pass_data:
            raise HTTPException(status_code=404, detail=f"Apple Pass '{serial_number}' not found")
            
        template_data = db.get_apple_template(pass_data.get('template_id', ''))
        
        from services.apple_wallet_service import AppleWalletService
        apple_service = AppleWalletService()
        
        class_data_for_service = {
            "class_type": "Generic",
            "template_id": pass_data.get('template_id', ''),
        }
        
        # Construct payload with pass data
        pkpass_path = apple_service.create_pass(
            class_data=class_data_for_service,
            pass_data=pass_data,
            object_id=serial_number,
        )
        
        if not os.path.exists(pkpass_path):
            raise HTTPException(status_code=500, detail="Generated PKPASS file not found on disk")
            
        return FileResponse(
            path=pkpass_path,
            filename=f"pass_{serial_number}.pkpass",
            media_type="application/vnd.apple.pkpass",
            headers={
                "Content-Disposition": f'attachment; filename="pass.pkpass"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
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
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=f"Pass '{pass_data.object_id}' already exists")
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except WalletPassError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail=f"Pass '{pass_data.object_id}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/passes/apple/", response_model=MessageResponse, status_code=201, tags=["Passes"])
async def create_apple_pass(pass_data: ApplePassCreate):
    """Create a new Apple Wallet pass"""
    try:
        # Verify template exists
        template_exists = db.get_apple_template(pass_data.template_id)
        if not template_exists:
            raise HTTPException(status_code=404, detail=f"Template '{pass_data.template_id}' not found")
        
        # Map fields from store_card_data if present (older structure) or pass_data
        # For our new relational 3-table structure, we expect fields_data as a list of dicts
        fields = []
        if pass_data.pass_data and "dynamic_fields" in pass_data.pass_data:
            # Map new dynamic fields format to DB format
            for i, f in enumerate(pass_data.pass_data["dynamic_fields"]):
                fields.append({
                    "type": f.get("field_type"),
                    "key": f.get("key", f"{f.get('field_type')}_{i}"),
                    "label": f.get("label", ""),
                    "value": f.get("value", "")
                })
        elif pass_data.pass_data and "textModulesData" in pass_data.pass_data:
            # Map generator format to DB format
            for m in pass_data.pass_data["textModulesData"]:
                # generator: {"id": "apple_sec", "header": "...", "body": "..."}
                # db expects: {"type": "secondary", "key": "...", "label": "...", "value": "..."}
                slot = m.get("id", "")
                f_type = "primary"
                if "header" in slot: f_type = "header"
                elif "sec" in slot: f_type = "secondary"
                elif "aux" in slot: f_type = "auxiliary"
                elif "back" in slot: f_type = "back"
                
                fields.append({
                    "type": f_type,
                    "key": slot,
                    "label": m.get("header", ""),
                    "value": m.get("body", "")
                })

        success = db.create_apple_pass(
            serial_number=pass_data.serial_number,
            template_id=pass_data.template_id,
            holder_name=pass_data.holder_name,
            holder_email=pass_data.holder_email,
            auth_token=pass_data.auth_token,
            status=pass_data.status.value,
            visual_data=pass_data.store_card_data,
            fields_data=fields
        )
        
        if success:
            return MessageResponse(
                message=f"Apple Pass '{pass_data.serial_number}' created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create Apple pass")
            
    except HTTPException:
        raise
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=f"Apple Pass '{pass_data.serial_number}' already exists")
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail=f"Apple Pass '{pass_data.serial_number}' already exists")
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
        logger.info(f"DEBUG: Searching for passes with email: '{email}'")
        passes = db.get_passes_by_email(email)
        logger.info(f"DEBUG: Found {len(passes)} passes")
        return passes
    except Exception as e:
        logger.error(f"DEBUG: Error searching passes by email: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.put("/passes/{object_id}", response_model=MessageResponse, tags=["Passes"])
async def update_pass(object_id: str, pass_update: PassUpdate, sync_to_google: bool = True, send_notification: bool = True):
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
                        
                        # Re-sync class template to Google (ensures classTemplateInfo
                        # front/back layout is up-to-date, e.g. first-2-rows-on-front)
                        try:
                            class_json = class_info.get('class_json', {})
                            if class_json and class_info.get('class_type') == 'Generic':
                                wallet_client.update_pass_class(
                                    class_id=updated_pass['class_id'],
                                    class_data=class_json,
                                    class_type='Generic'
                                )
                                logger.info(f"Re-synced class template for '{updated_pass['class_id']}'")
                        except Exception as cls_err:
                            logger.warning(f"Class template re-sync failed (non-fatal): {cls_err}")
                        
                        wallet_client.update_pass_object(
                            object_id=object_id,
                            class_id=updated_pass['class_id'],
                            holder_name=updated_pass['holder_name'],
                            holder_email=updated_pass['holder_email'],
                            pass_data=updated_pass.get('pass_data', {}),
                            class_type=class_info.get('class_type', 'Generic'),
                            send_notification=send_notification
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


@app.get("/passes/{object_id}/save-link", tags=["Passes"])
async def generate_pass_save_link(object_id: str):
    """Generate a Google Wallet JWT save link for a given pass"""
    try:
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
            
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet client missing")
            
        class_info = db.get_class(existing_pass['class_id'])
        if not class_info:
            raise HTTPException(status_code=404, detail="Class info missing for this pass.")
            
        logger.info(f"Generating save link for pass '{object_id}'")
        save_link = wallet_client.generate_save_link(
            object_id=object_id,
            class_type=class_info.get("class_type", "Generic"),
            class_id=class_info.get("class_id")
        )
        
        return {"save_link": save_link}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate save link: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate save link: {str(e)}")


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
        if not configs.ALLOW_GOOGLE_PASS_SYNC:
            raise HTTPException(
                status_code=403,
                detail="Syncing passes FROM Google is disabled. Set ALLOW_GOOGLE_PASS_SYNC=true to enable."
            )
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet service not initialized")
            
        logger.info("Starting pass objects sync from Google Wallet")

        def _extract_localized_value(v: Any) -> Optional[str]:
            """
            Google Wallet frequently uses LocalizedString/TranslatedString objects.
            This helper extracts a best-effort plain string value.
            """
            if v is None:
                return None
            if isinstance(v, str):
                return v
            if isinstance(v, (int, float, bool)):
                return str(v)
            if isinstance(v, dict):
                # Common shapes:
                # { defaultValue: { value: "..." } }
                dv = v.get("defaultValue")
                if isinstance(dv, dict):
                    val = dv.get("value")
                    if isinstance(val, str):
                        return val
                # Some objects use { value: "..." }
                val = v.get("value")
                if isinstance(val, str):
                    return val
            return None
        
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
                elif 'header' in google_pass:
                    # Generic object header is a localized string object
                    holder_name = _extract_localized_value(google_pass.get('header')) or holder_name
                
                if 'accountId' in google_pass:
                    holder_email = google_pass['accountId'] if isinstance(google_pass['accountId'], str) else ""
                
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

                # Normalize problematic dict fields into string-friendly shapes for DB storage.
                # Our DB schema stores only a few extracted scalar columns; any dict accidentally
                # mapped into those columns will break inserts/updates.
                if isinstance(pass_data_cleaned.get("header"), dict):
                    pass_data_cleaned["header_value"] = _extract_localized_value(pass_data_cleaned.get("header"))
                    pass_data_cleaned.pop("header", None)
                if isinstance(pass_data_cleaned.get("cardTitle"), dict):
                    pass_data_cleaned["subheader_value"] = _extract_localized_value(pass_data_cleaned.get("cardTitle"))
                    pass_data_cleaned.pop("cardTitle", None)
                
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
                        # Permanent behavior: do NOT fetch classes from Google during pass sync.
                        logger.warning(
                            f"Class '{local_class_id}' not found locally. "
                            f"Skipping pass '{object_id}' (class auto-fetch disabled)."
                        )
                        errors.append(f"Missing local class '{local_class_id}' for pass '{object_id}'")
                        continue
                         
                    try:
                        db.create_pass(
                            object_id=object_id,
                            class_id=local_class_id,
                            holder_name=holder_name,
                            holder_email=holder_email,
                            status=status,
                            pass_data=pass_data_cleaned
                        )
                    except Exception as create_err:
                        # Common failure: unique constraint (class_id, holder_email).
                        # Google Wallet can have multiple objects per class for the same accountId.
                        # If we hit that, fall back to a synthetic, object-scoped email to ensure
                        # we can still sync ALL objects by object_id.
                        err_str = str(create_err)
                        if "unique_class_holder" in err_str or "Duplicate entry" in err_str:
                            fallback_email = f"{holder_email.split('@')[0]}+{object_id}@{holder_email.split('@')[-1]}" if "@" in holder_email else f"unknown_{object_id}@example.com"
                            logger.warning(f"Unique constraint hit for class '{local_class_id}'. Retrying create with fallback email '{fallback_email}'.")
                            db.create_pass(
                                object_id=object_id,
                                class_id=local_class_id,
                                holder_name=holder_name,
                                holder_email=fallback_email,
                                status=status,
                                pass_data=pass_data_cleaned
                            )
                        else:
                            raise
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

# ========================================================================
# Notification Endpoints
# ========================================================================

@app.post("/passes/{object_id}/notify", response_model=MessageResponse, tags=["Passes"])
async def send_pass_notification(object_id: str, request: NotificationRequest):
    """Send a push notification to a specific pass holder"""
    try:
        # 1. Fetch pass from DB
        pass_data = db.get_pass(object_id)
        if not pass_data:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        # 2. Fetch class to get class_type
        class_data = db.get_class(pass_data['class_id'])
        if not class_data:
            raise HTTPException(status_code=404, detail=f"Class info for pass '{object_id}' not found")
            
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet client not initialized")
            
        # 3. Call wallet client to send notification using the ATOMIC update method.
        # This ensures the header is dynamic (Card Title) and the front field is updated.
        logger.info(f"Triggering Google Wallet notification for pass '{object_id}'")
        wallet_client.update_pass_object(
            object_id=object_id,
            class_id=pass_data['class_id'],
            holder_name=pass_data.get('holder_name', 'Pass Holder'),
            holder_email=pass_data.get('holder_email', ''),
            pass_data=pass_data.get('pass_data', {}),
            class_type=class_data['class_type'],
            notification_message=request.message,
            send_notification=True
        )
        
        # 4. Log to DB
        db.create_notification(
            class_id=pass_data['class_id'],
            object_id=object_id,
            status="Sent",
            message=f"Direct: {request.message}"
        )
        
        return MessageResponse(
            message=f"Notification sent to pass {object_id}",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/passes/apple/{serial_number}/notify", response_model=MessageResponse, tags=["Passes"])
async def send_apple_pass_notification(serial_number: str, request: NotificationRequest):
    """Send a silent push notification via APNs to all devices registered for this Apple pass."""
    try:
        from services.apple_wallet_service import AppleWalletService
        pass_data = db.get_apple_pass(serial_number)
        if not pass_data:
            raise HTTPException(status_code=404, detail=f"Apple pass '{serial_number}' not found")
        
        # 1. Update the message in the database for the lock-screen notification
        db.update_apple_pass_message(serial_number, request.message)
        
        # 2. Regenerate the pass file locally so the device fetches the updated content
        apple_service = AppleWalletService()
        template_id = pass_data.get('template_id', '')
        template_data = db.get_apple_template(template_id)
        
        class_data = {
            "class_type": "Generic",
            "template_id": template_id,
            "pass_style": template_data.get("pass_style", "eventTicket") if template_data else "eventTicket",
        }
        # Refetch updated pass_data from DB to get the new admin_message
        updated_pass_data = db.get_apple_pass(serial_number)
        
        apple_service.create_pass(
            class_data=class_data,
            pass_data=updated_pass_data,
            object_id=serial_number
        )
        
        # 3. Trigger the silent APNs push
        result = apple_service.send_push_notification(serial_number)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown APNs error"))
            
        return MessageResponse(
            message=f"Apple Lock-Screen Notification triggered. Success: {result['sent']}",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending Apple notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/templates/apple/{template_id}/notify", response_model=MessageResponse, tags=["Apple Templates"])
async def send_apple_template_notification(template_id: str, request: NotificationRequest):
    """Send a silent push notification via APNs to ALL passes belonging to an Apple template."""
    try:
        from services.apple_wallet_service import AppleWalletService
        
        template = db.get_apple_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Apple template '{template_id}' not found")
        
        # Fetch all apple passes for this template
        all_apple = db.get_all_apple_passes()
        template_passes = [p for p in all_apple if p.get("template_id") == template_id]
        
        if not template_passes:
            return MessageResponse(
                message=f"No passes found for template '{template_id}'.",
                success=True
            )
        
        apple_service = AppleWalletService()
        sent_count = 0
        
        for p in template_passes:
            serial = p.get("serial_number")
            if not serial: continue
            
            # 1. Update the message in the database 
            db.update_apple_pass_message(serial, request.message)
            
            # 2. Regenerate the pass
            template_info = db.get_apple_template(template_id)
            class_data = {
                "class_type": "Generic",
                "template_id": template_id,
                "pass_style": template_info.get("pass_style", "eventTicket") if template_info else "eventTicket",
            }
            updated_p = db.get_apple_pass(serial)
            apple_service.create_pass(class_data=class_data, pass_data=updated_p, object_id=serial)
            
            # 3. Trigger APNs
            result = apple_service.send_push_notification(serial)
            if result.get("sent"):
                sent_count += 1
                
        return MessageResponse(
            message=f"Bulk Apple Lock-Screen Notification triggered for {sent_count} devices.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk Apple notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/passes/apple/{serial_number}/devices", tags=["Passes"])
async def get_apple_pass_devices_count(serial_number: str):
    """Get the count of devices registered for push updates on this pass."""
    try:
        push_tokens = db.get_registered_devices_for_pass(serial_number)
        return {"serial_number": serial_number, "count": len(push_tokens)}
    except Exception as e:
        logger.error(f"Error fetching registered devices count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classes/{class_id}/notify", response_model=MessageResponse, tags=["Classes"])
async def send_class_notification(class_id: str, request: NotificationRequest):
    """Send a push notification to all holders of a template/class"""
    try:
        # 1. Verify class exists
        class_data = db.get_class(class_id)
        if not class_data:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
            
        if not wallet_client:
            raise HTTPException(status_code=503, detail="Google Wallet client not initialized")
            
        # 2. Use existing propagation service to send bulk notifications
        # This service already handles fetching passes, sending via wallet_client, and logging to DB.
        result = propagate_class_update_to_passes(
            class_id=class_id,
            updated_class=class_data,
            db_manager=db,
            wallet_client=wallet_client,
            notification_message=request.message
        )
        
        message = (
            f"Bulk notification sent. "
            f"Success: {result['updated_count']}, "
            f"Failed: {result['failed_count']}."
        )
        
        return MessageResponse(
            message=message,
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Apple Web Service V1 Endpoints (APNs & Wallet Updates)
# ========================================================================

def _verify_apple_auth(request: Request, serial_number: str) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("ApplePass "):
        logger.warning(f"APPLE AUTH: Missing or invalid Header for serial {serial_number}")
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid Authorization header")
    
    token = auth_header[len("ApplePass "):]
    pass_data = db.get_apple_pass(serial_number)
    
    db_token = pass_data.get("auth_token") if pass_data else None
    
    # Log detailed auth attempt for debugging
    with open("apple_wallet_logs.txt", "a") as f:
        f.write(f"[{datetime.now()}] AUTH CHECK: Serial={serial_number}, IncomingToken={token}, DBToken={db_token}\n")
    
    if not pass_data or db_token != token:
        logger.error(f"APPLE AUTH FAILED for {serial_number}")
        raise HTTPException(status_code=401, detail="Unauthorized: Token mismatch or pass not found")
        
    return pass_data

@app.post("/v1/log", tags=["Apple Web Service"])
async def log_apple_messages(request: Request):
    """Endpoint for Apple Wallet devices to send their logs and errors to."""
    body = await request.json()
    
    with open("apple_wallet_logs.txt", "a") as f:
        f.write(f"\n================================\nAPPLE WALLET LOGS\n================================\n")
        for index, log_entry in enumerate(body.get('logs', [])):
            f.write(f"[{index}] {log_entry}\n")
        f.write("================================\n\n")
        
    return Response(status_code=200)

@app.post("/v1/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}", tags=["Apple Web Service"])
async def register_apple_device(
    device_library_id: str, 
    pass_type_id: str, 
    serial_number: str, 
    registration: AppleRegistrationRequest,
    request: Request
):
    """Register a device to receive push notifications for a pass"""
    try:
        _verify_apple_auth(request, serial_number)
        logger.info(f"Registering device {device_library_id} for pass {serial_number} with token {registration.pushToken}")
        
        success = db.register_apple_device(device_library_id, registration.pushToken, pass_type_id, serial_number)
        if success:
            return Response(status_code=201)
        return Response(status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering apple device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/v1/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}", tags=["Apple Web Service"])
async def unregister_apple_device(
    device_library_id: str, 
    pass_type_id: str, 
    serial_number: str, 
    request: Request
):
    """Unregister a device (user deleted the pass)"""
    try:
        _verify_apple_auth(request, serial_number)
        logger.info(f"Unregistering device {device_library_id} for pass {serial_number}")
        
        db.unregister_apple_device(device_library_id, serial_number)
        return Response(status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering apple device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/devices/{device_library_id}/registrations/{pass_type_id}", tags=["Apple Web Service"])
async def get_serial_numbers_for_device(
    device_library_id: str,
    pass_type_id: str,
    request: Request
):
    """Return serial numbers for passes registered to a device."""
    try:
        passes_updated_since = request.query_params.get("passesUpdatedSince")
        print(f"🍏 [V1-SERIALS] Device {device_library_id[:10]}... checking for updates (since: {passes_updated_since})")
        logger.info(f"APPLE: Device {device_library_id} requested serials for {pass_type_id} (UpdatedSince: {passes_updated_since})")
        
        if passes_updated_since:
            try:
                # Try parsing ISO format
                since_dt = datetime.fromisoformat(passes_updated_since.replace(' ', '+'))
            except (ValueError, TypeError):
                # Try parsing as unix timestamp if provided as number
                try:
                    since_dt = datetime.fromtimestamp(float(passes_updated_since))
                except (ValueError, TypeError):
                    # Fallback to a safe minimum for MariaDB TIMESTAMP (1970)
                    since_dt = datetime(1970, 1, 1)
            
            serial_numbers = db.get_apple_passes_updated_since(
                pass_type_id=pass_type_id,
                device_library_id=device_library_id,
                passes_updated_since=since_dt
            )
        else:
            serial_numbers = db.get_passes_by_device(
                device_library_id=device_library_id,
                pass_type_id=pass_type_id
            )
        
        if not serial_numbers:
            print(f"🍏 [V1-SERIALS] → No updated passes found. Returning 204.")
            logger.info(f"APPLE: No updated passes for device {device_library_id}")
            return Response(status_code=204)
        
        last_updated = datetime.now().isoformat()
        print(f"🍏 [V1-SERIALS] → Found {len(serial_numbers)} updated pass(es): {serial_numbers}")
        
        return {
            "serialNumbers": serial_numbers,
            "lastUpdated": last_updated
        }
    except Exception as e:
        import traceback
        err_detail = traceback.format_exc()
        logger.error(f"Error in get_serial_numbers_for_device: {e}\n{err_detail}")
        with open("apple_wallet_logs.txt", "a") as f:
            f.write(f"[{datetime.now()}] 500 ERROR in get_serial_numbers_for_device: {e}\n{err_detail}\n")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/v1/passes/{pass_type_id}/{serial_number}", tags=["Apple Web Service"])
async def get_updated_apple_pass(
    pass_type_id: str, 
    serial_number: str, 
    request: Request
):
    """Generate and return the latest updated .pkpass file to the device"""
    from fastapi.responses import FileResponse
    import os
    try:
        pass_data = _verify_apple_auth(request, serial_number)
        print(f"🍏 [V1-UPDATE] Device '{request.headers.get('User-Agent')}' is downloading updated pass: {serial_number}")
        logger.info(f"Device requesting updated pass {serial_number}")
        
        template_data = db.get_apple_template(pass_data.get('template_id', ''))
        
        from services.apple_wallet_service import AppleWalletService
        apple_service = AppleWalletService()
        
        class_data_for_service = {
            "class_type": "Generic",
            "template_id": pass_data.get('template_id', ''),
            "pass_style": template_data.get("pass_style", "eventTicket") if template_data else "eventTicket",
        }
        
        pass_payload = pass_data.get("visual_data", {})
        if not isinstance(pass_payload, dict):
            pass_payload = {}
        pass_payload["dynamic_fields"] = pass_data.get("fields", [])
        
        pkpass_path = apple_service.create_pass(
            class_data=class_data_for_service,
            pass_data=pass_data,
            object_id=serial_number,
        )
        
        if not os.path.exists(pkpass_path):
            raise HTTPException(status_code=500, detail="Generated PKPASS file not found on disk")
            
        modified_time = os.path.getmtime(pkpass_path)
        # Convert timestamp to true UTC (GMT) for the header
        last_modified = datetime.fromtimestamp(modified_time, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return FileResponse(
            path=pkpass_path,
            filename=f"pass_{serial_number}.pkpass",
            media_type="application/vnd.apple.pkpass",
            headers={
                "Last-Modified": last_modified,
                "Content-Disposition": f'attachment; filename="pass.pkpass"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating pass for update: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# QR Campaign Endpoints
# ========================================================================

@app.post("/campaigns/", response_model=MessageResponse, status_code=201, tags=["Campaigns"])
async def create_campaign(campaign_data: QRCampaignCreate):
    """Create a new QR Campaign"""
    try:
        success = db.create_campaign(
            campaign_name=campaign_data.campaign_name,
            slug=campaign_data.slug,
            google_class_id=campaign_data.google_class_id,
            apple_template_id=campaign_data.apple_template_id,
            landing_title=campaign_data.landing_title,
            landing_subtitle=campaign_data.landing_subtitle
        )
        if success:
            invalidate_campaign_cache(campaign_data.slug)
            return MessageResponse(message=f"Campaign '{campaign_data.campaign_name}' created", success=True)
        raise HTTPException(status_code=400, detail="Failed to create campaign")
    except Exception as e:
        if "Duplicate entry" in str(e):
             raise HTTPException(status_code=409, detail=f"Slug '{campaign_data.slug}' already exists")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/", response_model=List[QRCampaignResponse], tags=["Campaigns"])
async def get_all_campaigns():
    """List all campaigns"""
    return db.get_all_campaigns()

@app.get("/campaigns/{slug_or_id}", response_model=QRCampaignResponse, tags=["Campaigns"])
async def get_campaign(slug_or_id: str):
    """Get a specific campaign"""
    c = get_cached_campaign(slug_or_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c

@app.put("/campaigns/{campaign_id}", response_model=MessageResponse, tags=["Campaigns"])
async def update_campaign(campaign_id: int, campaign_data: QRCampaignUpdate):
    """Update a campaign"""
    update_dict = campaign_data.model_dump(exclude_unset=True)
    success = db.update_campaign(campaign_id, **update_dict)
    if success:
        invalidate_campaign_cache() # Clear all to be safe or find specific slug
        return MessageResponse(message="Campaign updated", success=True)
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.delete("/campaigns/{campaign_id}", response_model=MessageResponse, tags=["Campaigns"])
async def delete_campaign(campaign_id: int):
    """Delete a campaign"""
    success = db.delete_campaign(campaign_id)
    if success:
        invalidate_campaign_cache()
        return MessageResponse(message="Campaign deleted", success=True)
    raise HTTPException(status_code=404, detail="Campaign not found")


# ========================================================================
# Public Scanning & Pass Generation
# ========================================================================

@app.get("/c/{slug}", tags=["Public"])
async def campaign_landing(request: Request, slug: str):
    """Public landing page for a QR scan"""
    campaign = get_cached_campaign(slug)
    if not campaign or not campaign.get('is_active'):
        raise HTTPException(status_code=404, detail="Campaign not found or inactive")
    
    # Get template/class info for branding
    google_class = db.get_class(campaign['google_class_id']) if campaign['google_class_id'] else None
    apple_template = db.get_apple_template(campaign['apple_template_id']) if campaign['apple_template_id'] else None
    
    # Determine which branding to show if both exist (favor Apple images usually)
    logo_url = (apple_template or {}).get('logo_url') or (google_class or {}).get('logo_url')
    hero_url = (google_class or {}).get('hero_image_url') or (apple_template or {}).get('background_image_url')
    
    return templates.TemplateResponse("scan_landing.html", {
        "request": request,
        "campaign": campaign,
        "logo_url": logo_url,
        "hero_url": hero_url,
        "slug": slug
    })

@app.post("/c/{slug}", tags=["Public"])
async def generate_campaign_pass(request: Request, slug: str):
    """Process landing page form and return wallet link/pass"""
    form_data = await request.form()
    holder_name = form_data.get("name")
    holder_email = form_data.get("email")
    
    if not holder_name or not holder_email:
        raise HTTPException(status_code=400, detail="Name and Email are required")
        
    campaign = get_cached_campaign(slug)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    user_agent = request.headers.get("User-Agent", "").lower()
    is_ios = "iphone" in user_agent or "ipad" in user_agent or "macintosh" in user_agent
    
    # 1. GENERATE APPLE PASS
    if is_ios:
        if not campaign.get('apple_template_id'):
            # Fallback to Google if no Apple template defined
            return await _generate_google_link(campaign, holder_name, holder_email)
            
        import uuid
        serial_number = f"c_{slug}_{uuid.uuid4().hex[:8]}"
        auth_token = uuid.uuid4().hex
        
        # Create in DB
        success = db.create_apple_pass(
            serial_number=serial_number,
            template_id=campaign['apple_template_id'],
            holder_name=holder_name,
            holder_email=holder_email,
            auth_token=auth_token,
            visual_data=db.get_apple_template(campaign['apple_template_id'])
        )
        
        if success:
            # Generate .pkpass
            from services.apple_wallet_service import AppleWalletService
            apple_service = AppleWalletService()
            
            # Re-fetch for full data
            pass_data = db.get_apple_pass(serial_number)
            template_data = db.get_apple_template(campaign['apple_template_id'])
            
            apple_service.create_pass(
                class_data={
                    "class_type": template_data.get("pass_style", "storeCard"),
                    "template_id": campaign['apple_template_id']
                },
                pass_data=pass_data,
                object_id=serial_number
            )
            
            # Redirect to download
            return Response(
                headers={"Location": f"/passes/apple/{serial_number}/download"},
                status_code=303
            )
            
    # 2. GENERATE GOOGLE LINK (Android or fallback)
    return await _generate_google_link(campaign, holder_name, holder_email)

async def _generate_google_link(campaign, name, email):
    if not campaign.get('google_class_id'):
        raise HTTPException(status_code=500, detail="No Google Class linked to this campaign")
        
    import uuid
    object_id = f"{configs.ISSUER_ID}.g_{campaign['slug']}_{uuid.uuid4().hex[:8]}"
    
    # Create in DB
    success = db.create_pass(
        object_id=object_id,
        class_id=campaign['google_class_id'],
        holder_name=name,
        holder_email=email,
        pass_data={} # Add default metadata from class if needed
    )
    
    if success:
        if wallet_client:
             # Fetch the synthesized class_json logic is usually in db_manager
             pass_data = db.get_pass(object_id)
             google_link = wallet_client.generate_save_link(
                 class_id=campaign['google_class_id'],
                 object_id=object_id,
                 holder_name=name,
                 holder_email=email,
                 pass_data=pass_data.get('pass_data', {})
             )
             return Response(headers={"Location": google_link}, status_code=303)
    
    raise HTTPException(status_code=500, detail="Failed to generate Google Wallet link")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)

