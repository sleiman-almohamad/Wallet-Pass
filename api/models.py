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
    # Common fields
    issuer_name: Optional[str] = Field(None, description="Name of the issuer/business")
    base_color: Optional[str] = Field(None, description="Hex color code (e.g., '#FF5733')")
    logo_url: Optional[str] = Field(None, description="URL to the class logo")
    hero_image_url: Optional[str] = Field(None, description="Hero image URL")
    # Generic-specific
    header_text: Optional[str] = Field(None, description="Header text (Generic)")
    card_title: Optional[str] = Field(None, description="Card title (Generic)")
    # EventTicket-specific
    event_name: Optional[str] = Field(None, description="Event name")
    venue_name: Optional[str] = Field(None, description="Venue name")
    venue_address: Optional[str] = Field(None, description="Venue address")
    event_start: Optional[str] = Field(None, description="Event start datetime")
    # Loyalty-specific
    program_name: Optional[str] = Field(None, description="Loyalty program name")
    # Transit-specific
    transit_type: Optional[str] = Field(None, description="Transit type (e.g., TRANSIT_TYPE_BUS)")
    transit_operator_name: Optional[str] = Field(None, description="Transit operator name")
    # Legacy compat
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
                    "event_name": "My Event"
                }
            ]
        }
    }


class ClassUpdate(BaseModel):
    """Model for updating a pass class"""
    class_type: Optional[str] = Field(None, description="Type of pass")
    issuer_name: Optional[str] = Field(None, description="Name of the issuer/business")
    base_color: Optional[str] = Field(None, description="Hex color code")
    logo_url: Optional[str] = Field(None, description="URL to the class logo")
    hero_image_url: Optional[str] = Field(None, description="Hero image URL")
    header_text: Optional[str] = Field(None, description="Header text (Generic)")
    card_title: Optional[str] = Field(None, description="Card title (Generic)")
    event_name: Optional[str] = Field(None, description="Event name")
    venue_name: Optional[str] = Field(None, description="Venue name")
    venue_address: Optional[str] = Field(None, description="Venue address")
    event_start: Optional[str] = Field(None, description="Event start datetime")
    program_name: Optional[str] = Field(None, description="Loyalty program name")
    transit_type: Optional[str] = Field(None, description="Transit type")
    transit_operator_name: Optional[str] = Field(None, description="Transit operator name")
    class_json: Optional[Dict[str, Any]] = Field(None, description="Complete Google Wallet class JSON configuration")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "issuer_name": "Updated Business Name",
                    "base_color": "#00FF00"
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
# Sub-Models for Passes
# ========================================================================

class TextModuleModel(BaseModel):
    id: Optional[str] = None
    header: Optional[str] = None
    body: Optional[str] = None

class MessageModel(BaseModel):
    id: Optional[str] = None
    header: Optional[str] = None
    body: Optional[str] = None
    messageType: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class EventTicketDataModel(BaseModel):
    ticket_holder_name: Optional[str] = Field(None, alias="ticketHolderName")
    confirmation_code: Optional[str] = Field(None, alias="confirmationCode")
    seat: Optional[str] = Field(None, alias="seatNumber")
    section: Optional[str] = None
    gate: Optional[str] = None
    
    class Config:
        populate_by_name = True

class GenericDataModel(BaseModel):
    header_value: Optional[str] = None
    subheader_value: Optional[str] = None


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
    
    # Optional relational data
    event_ticket_data: Optional[EventTicketDataModel] = None
    generic_data: Optional[GenericDataModel] = None
    text_modules: Optional[list[TextModuleModel]] = Field(default_factory=list, alias="textModulesData")
    messages: Optional[list[MessageModel]] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class PassUpdate(BaseModel):
    """Model for updating a pass - simplified for local DB updates"""
    holder_name: Optional[str] = Field(None, description="Name of the pass holder")
    holder_email: Optional[str] = Field(None, description="Email of the pass holder")
    status: Optional[PassStatus] = Field(None, description="Pass status")
    pass_data: Optional[Dict[str, Any]] = Field(None, description="Pass-specific data fields")


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
    object_id: str
    class_id: str
    holder_name: str
    holder_email: str
    status: str
    sync_status: Optional[str] = "pending"
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    
    # Relational data properties
    event_ticket_data: Optional[EventTicketDataModel] = None
    generic_data: Optional[GenericDataModel] = None
    text_modules: Optional[list[TextModuleModel]] = Field(default_factory=list, alias="textModulesData")
    messages: Optional[list[MessageModel]] = Field(default_factory=list)
    
    # Fallback/computed dictionary object mimicking the old schema pass_data so UI continues working
    pass_data: Optional[Dict[str, Any]] = None
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
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
