"""
Google Wallet Class Parser
Extracts field definitions and metadata from Google Wallet class JSON
"""

def parse_google_wallet_class(class_json):
    """
    Parse Google Wallet class JSON to extract metadata
    
    Args:
        class_json: The class object from Google Wallet API
        
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        'class_id': class_json.get('id', ''),
        'class_type': 'Generic',
        'base_color': None,
        'logo_url': None
    }
    
    # Determine class type from the JSON structure
    if 'eventName' in class_json:
        metadata['class_type'] = 'EventTicket'
    elif 'programName' in class_json:
        metadata['class_type'] = 'LoyaltyCard'
    elif 'merchantName' in class_json and 'cardNumber' in class_json:
        metadata['class_type'] = 'GiftCard'
    elif 'transitType' in class_json:
        metadata['class_type'] = 'TransitPass'
    
    # Extract background color
    if 'hexBackgroundColor' in class_json:
        metadata['base_color'] = class_json['hexBackgroundColor']
    
    # Extract logo URL
    if 'logo' in class_json:
        logo = class_json['logo']
        if 'sourceUri' in logo and 'uri' in logo['sourceUri']:
            metadata['logo_url'] = logo['sourceUri']['uri']
    
    return metadata


def extract_field_hints_from_class(class_json):
    """
    Extract field hints and default values from Google Wallet class
    This can be used to pre-populate or suggest values
    
    Args:
        class_json: The class object from Google Wallet API
        
    Returns:
        Dictionary of field hints
    """
    hints = {}
    
    # Extract event-specific hints
    if 'eventName' in class_json:
        event_name = class_json['eventName']
        if isinstance(event_name, dict) and 'defaultValue' in event_name:
            hints['event_name'] = event_name['defaultValue'].get('value', '')
    
    if 'venue' in class_json:
        venue = class_json['venue']
        if isinstance(venue, dict):
            if 'name' in venue:
                venue_name = venue['name']
                if isinstance(venue_name, dict) and 'defaultValue' in venue_name:
                    hints['venue'] = venue_name['defaultValue'].get('value', '')
    
    # Extract loyalty-specific hints
    if 'programName' in class_json:
        program_name = class_json['programName']
        if isinstance(program_name, dict) and 'defaultValue' in program_name:
            hints['program_name'] = program_name['defaultValue'].get('value', '')
    
    return hints
