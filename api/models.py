"""
Pydantic Models for FastAPI Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PassStatus(str, Enum):
    """Enum for pass status"""
    ACTIVE = "Active"
    EXPIRED = "Expired"


# ========================================================================
# Class Models
# ========================================================================

class ClassCreate(BaseModel):
    """Model for creating a new pass class"""
    class_id: str = Field(..., description="Unique identifier for the class")
    class_type: str = Field(..., description="Type of pass (e.g., 'EventTicket', 'LoyaltyCard')")
    base_color: Optional[str] = Field(None, description="Hex color code (e.g., '#FF5733')")
    logo_url: Optional[str] = Field(None, description="URL to the class logo")
    issuer_name: Optional[str] = Field(None, description="Name of the issuer/business")
    header_text: Optional[str] = Field(None, description="Header text for the pass")
    card_title: Optional[str] = Field(None, description="Card title for the pass")
    class_json: Optional[Dict[str, Any]] = Field(None, description="Complete Google Wallet class JSON configuration")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "class_id": "EVENT_CLASS_001",
                    "class_type": "EventTicket",
                    "base_color": "#FF5733",
                    "logo_url": "https://example.com/logo.png",
                    "issuer_name": "My Business",
                    "header_text": "Business Name",
                    "card_title": "Event Pass"
                }
            ]
        }
    }


class ClassUpdate(BaseModel):
    """Model for updating a pass class"""
    class_type: Optional[str] = Field(None, description="Type of pass")
    base_color: Optional[str] = Field(None, description="Hex color code")
    logo_url: Optional[str] = Field(None, description="URL to the class logo")
    issuer_name: Optional[str] = Field(None, description="Name of the issuer/business")
    header_text: Optional[str] = Field(None, description="Header text for the pass")
    card_title: Optional[str] = Field(None, description="Card title for the pass")
    class_json: Optional[Dict[str, Any]] = Field(None, description="Complete Google Wallet class JSON configuration")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "base_color": "#00FF00",
                    "logo_url": "https://example.com/new-logo.png",
                    "issuer_name": "Updated Business Name",
                    "header_text": "New Header",
                    "card_title": "New Title"
                }
            ]
        }
    }


class ClassResponse(BaseModel):
    """Model for class response"""
    class_id: str
    class_type: str
    base_color: Optional[str] = None
    logo_url: Optional[str] = None
    issuer_name: Optional[str] = None
    header_text: Optional[str] = None
    card_title: Optional[str] = None
    class_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ========================================================================
# Pass Models
# ========================================================================

class PassCreate(BaseModel):
    """Model for creating a new pass"""
    object_id: str = Field(..., description="Unique identifier for the pass object")
    class_id: str = Field(..., description="Reference to the class")
    holder_name: str = Field(..., description="Name of the pass holder")
    holder_email: EmailStr = Field(..., description="Email of the pass holder")
    status: PassStatus = Field(PassStatus.ACTIVE, description="Pass status")
    pass_data: Optional[Dict[str, Any]] = Field(None, description="Additional JSON data")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "object_id": "PASS_001",
                    "class_id": "EVENT_CLASS_001",
                    "holder_name": "John Doe",
                    "holder_email": "john.doe@example.com",
                    "status": "Active",
                    "pass_data": {
                        "seat": "A12",
                        "gate": "Gate 5",
                        "match_time": "2024-12-15T19:00:00"
                    }
                }
            ]
        }
    }


class PassUpdate(BaseModel):
    """Model for updating a pass"""
    holder_name: Optional[str] = Field(None, description="Name of the pass holder")
    holder_email: Optional[EmailStr] = Field(None, description="Email of the pass holder")
    status: Optional[PassStatus] = Field(None, description="Pass status")
    pass_data: Optional[Dict[str, Any]] = Field(None, description="Additional JSON data")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "holder_name": "Jane Doe",
                    "status": "Expired"
                }
            ]
        }
    }


class PassStatusUpdate(BaseModel):
    """Model for updating pass status only"""
    status: PassStatus = Field(..., description="New pass status")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "Expired"
                }
            ]
        }
    }


class PassResponse(BaseModel):
    """Model for pass response"""
    id: int
    object_id: str
    class_id: str
    holder_name: str
    holder_email: str
    status: str
    pass_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ========================================================================
# Utility Models
# ========================================================================

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    database: str
    timestamp: datetime
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "database": "connected",
                    "timestamp": "2024-12-09T08:00:00"
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Model for generic message responses"""
    message: str
    success: bool = True
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Operation completed successfully",
                    "success": True
                }
            ]
        }
    }
