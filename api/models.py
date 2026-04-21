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
    text_module_rows: Optional[list['TextModuleRowModel']] = Field(default_factory=list, description="Array of text module rows")
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
    text_module_rows: Optional[list['TextModuleRowModel']] = Field(default_factory=list, description="Array of text module rows")
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
    text_module_rows: Optional[list['TextModuleRowModel']] = Field(default_factory=list)
    class_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ========================================================================
# Apple Template Models
# ========================================================================

class AppleTemplateCreate(BaseModel):
    """Model for creating a new Apple Wallet template"""
    template_id: str = Field(..., description="Unique identifier for the template")
    template_name: str = Field(..., description="Human-readable name for the template")
    pass_style: str = Field(..., description="Apple Pass style (e.g., 'storeCard', 'boardingPass')")
    pass_type_identifier: str = Field(..., description="Apple Pass Type Identifier (e.g., 'pass.com.example')")
    team_identifier: str = Field(..., description="Apple Team Identifier")

class AppleTemplateUpdate(BaseModel):
    """Model for updating an Apple Wallet template"""
    template_name: Optional[str] = None
    pass_style: Optional[str] = None
    pass_type_identifier: Optional[str] = None
    team_identifier: Optional[str] = None

class AppleTemplateResponse(BaseModel):
    """Model for Apple Template response"""
    template_id: str
    template_name: str
    pass_style: str
    pass_type_identifier: str
    team_identifier: str
    created_at: datetime
    updated_at: datetime

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
    module_type: Optional[str] = None

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


class TextModuleRowModel(BaseModel):
    row_index: Optional[int] = None
    left_header: Optional[str] = None
    left_body: Optional[str] = None
    left_type: Optional[str] = None
    middle_header: Optional[str] = None
    middle_body: Optional[str] = None
    middle_type: Optional[str] = None
    right_header: Optional[str] = None
    right_body: Optional[str] = None
    right_type: Optional[str] = None

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
    # Legacy/compat: the project’s UI/API client posts an unstructured `pass_data` dict.
    # The backend uses `pass_data.pass_data` when persisting/syncing.
    pass_data: Optional[Dict[str, Any]] = Field(None, description="Pass-specific data fields")
    
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


class ApplePassCreate(BaseModel):
    """Model for creating a new Apple Wallet pass"""
    serial_number: str = Field(..., description="Unique serial number for the pass")
    template_id: str = Field(..., description="Reference to the template")
    pass_type_id: str = Field(..., description="Apple Pass Type ID")
    holder_name: str = Field(..., description="Name of the pass holder")
    holder_email: EmailStr = Field(..., description="Email of the pass holder")
    status: PassStatus = Field(PassStatus.ACTIVE, description="Pass status")
    auth_token: str = Field(..., description="Authentication token for the pass")
    pass_data: Optional[Dict[str, Any]] = Field(None, description="Pass-specific data fields")
    store_card_data: Optional[Dict[str, Any]] = Field(None, description="Visual data for the pass")


class ApplePassFieldResponse(BaseModel):
    """Model for relational fields inside an Apple Pass"""
    type: str
    key: str
    label: Optional[str] = None
    value: str


class ApplePassResponse(BaseModel):
    """Model for Apple Pass response"""
    serial_number: str
    template_id: str
    holder_name: str
    holder_email: str
    status: str
    auth_token: Optional[str] = None
    background_color: Optional[str] = None
    foreground_color: Optional[str] = None
    label_color: Optional[str] = None
    organization_name: Optional[str] = None
    logo_text: Optional[str] = None
    logo_url: Optional[str] = None
    icon_url: Optional[str] = None
    strip_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    fields: list[ApplePassFieldResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }


class ApplePassUpdate(BaseModel):
    """Model for updating an Apple Pass"""
    holder_name: Optional[str] = None
    holder_email: Optional[str] = None
    status: Optional[PassStatus] = None
    background_color: Optional[str] = None
    foreground_color: Optional[str] = None
    label_color: Optional[str] = None
    organization_name: Optional[str] = None
    logo_text: Optional[str] = None
    logo_url: Optional[str] = None
    icon_url: Optional[str] = None
    strip_url: Optional[str] = None
    background_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ticket_layout: Optional[str] = None
    fields: Optional[list[ApplePassFieldResponse]] = None
    # Accept dynamic_fields from UI (list of {field_type, label, value})
    dynamic_fields: Optional[list[dict]] = None
    # Accept per-type field lists from UI
    header_fields: Optional[list[dict]] = None
    primary_fields: Optional[list[dict]] = None
    secondary_fields: Optional[list[dict]] = None
    auxiliary_fields: Optional[list[dict]] = None
    back_fields: Optional[list[dict]] = None


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


class NotificationRequest(BaseModel):
    """Model for sending a push notification"""
    message: str = Field(..., description="The notification message text")


class AppleRegistrationRequest(BaseModel):
    """Model for registering an Apple device for push notifications"""
    pushToken: str = Field(..., description="The APNs push token for the device")
