"""
FastAPI Application for Wallet Passes
Provides RESTful API endpoints for managing pass classes and passes
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
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
        success = db.create_class(
            class_id=class_data.class_id,
            class_type=class_data.class_type,
            base_color=class_data.base_color,
            logo_url=class_data.logo_url
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
    """Update a pass class"""
    try:
        # Check if class exists
        existing_class = db.get_class(class_id)
        if not existing_class:
            raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found")
        
        # Only update fields that are provided
        update_data = class_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = db.update_class(class_id, **update_data)
        
        if success:
            return MessageResponse(
                message=f"Class '{class_id}' updated successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update class")
            
    except HTTPException:
        raise
    except Exception as e:
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
async def update_pass(object_id: str, pass_data: PassUpdate):
    """Update a pass"""
    try:
        # Check if pass exists
        existing_pass = db.get_pass(object_id)
        if not existing_pass:
            raise HTTPException(status_code=404, detail=f"Pass '{object_id}' not found")
        
        # Only update fields that are provided
        update_data = pass_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Convert status enum to string if present
        if 'status' in update_data:
            update_data['status'] = update_data['status'].value
        
        success = db.update_pass(object_id, **update_data)
        
        if success:
            return MessageResponse(
                message=f"Pass '{object_id}' updated successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update pass")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)
