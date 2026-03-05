"""
Field Schema Definitions for Different Pass Types
Defines the structure of dynamic fields for each class type
"""

# Field schema for different class types
CLASS_FIELD_SCHEMAS = {
    "EventTicket": [
        {"name": "seat", "label": "Seat Number", "type": "text", "hint": "e.g., A12"},
        {"name": "section", "label": "Section", "type": "text", "hint": "e.g., North Stand"},
        {"name": "row", "label": "Row", "type": "text", "hint": "e.g., 5"},
        {"name": "gate", "label": "Gate", "type": "text", "hint": "e.g., Gate 5"},
        {"name": "match_time", "label": "Event Time", "type": "datetime", "hint": "e.g., 2024-12-15T19:00:00"},
        {"name": "venue", "label": "Venue", "type": "text", "hint": "e.g., Stadium Name"},
    ],
    "LoyaltyCard": [
        {"name": "member_id", "label": "Member ID", "type": "text", "hint": "e.g., MEMBER123"},
        {"name": "points", "label": "Points", "type": "number", "hint": "e.g., 1000"},
        {"name": "tier", "label": "Tier", "type": "text", "hint": "e.g., Gold, Silver, Bronze"},
        {"name": "expiry_date", "label": "Expiry Date", "type": "date", "hint": "e.g., 2025-12-31"},
    ],
    "GiftCard": [
        {"name": "balance", "label": "Balance", "type": "number", "hint": "e.g., 50.00"},
        {"name": "card_number", "label": "Card Number", "type": "text", "hint": "e.g., 1234-5678-9012"},
        {"name": "expiry_date", "label": "Expiry Date", "type": "date", "hint": "e.g., 2025-12-31"},
    ],
    "TransitPass": [
        {"name": "pass_type", "label": "Pass Type", "type": "text", "hint": "e.g., Monthly, Weekly"},
        {"name": "zone", "label": "Zone", "type": "text", "hint": "e.g., Zone 1-2"},
        {"name": "valid_from", "label": "Valid From", "type": "date", "hint": "e.g., 2024-12-01"},
        {"name": "valid_until", "label": "Valid Until", "type": "date", "hint": "e.g., 2024-12-31"},
    ],
    "Generic": [
        {"name": "field1", "label": "Field 1", "type": "text", "hint": "Custom field 1"},
        {"name": "field2", "label": "Field 2", "type": "text", "hint": "Custom field 2"},
        {"name": "field3", "label": "Field 3", "type": "text", "hint": "Custom field 3"},
    ]
}


def get_fields_for_class_type(class_type: str):
    """
    Get field schema for a given class type
    Returns default Generic schema if class type not found
    """
    return CLASS_FIELD_SCHEMAS.get(class_type, CLASS_FIELD_SCHEMAS["Generic"])
