"""
Google Wallet Class Parser
Extracts field definitions and metadata from Google Wallet class JSON
"""

def parse_google_wallet_class(class_json):
    """
    Parse Google Wallet class JSON to extract metadata for relational storage.
    Returns fields for both parent (Classes_Table) and child tables.
    """
    metadata = {
        # Parent table fields
        'class_id': class_json.get('id', ''),
        'class_type': 'Generic',
        'issuer_name': None,
        'base_color': None,
        'logo_url': None,
        'hero_image_url': None,
        # Generic child fields
        'header_text': None,
        'card_title': None,
        # EventTicket child fields
        'event_name': None,
        'venue_name': None,
        'venue_address': None,
        'event_start': None,
        # Loyalty child fields
        'program_name': None,
        # Transit child fields
        'transit_type': None,
        'transit_operator_name': None,
    }
    
    # Strip issuer ID prefix if present
    import configs
    if metadata['class_id'].startswith(f"{configs.ISSUER_ID}."):
        metadata['class_id'] = metadata['class_id'][len(configs.ISSUER_ID)+1:]
    
    # Determine class type from the JSON structure
    if 'eventName' in class_json:
        metadata['class_type'] = 'EventTicket'
    elif 'programName' in class_json:
        metadata['class_type'] = 'LoyaltyCard'
    elif 'merchantName' in class_json and 'cardNumber' in class_json:
        metadata['class_type'] = 'GiftCard'
    elif 'transitType' in class_json:
        metadata['class_type'] = 'TransitPass'
    
    # ---- Common (parent) fields ----
    if 'hexBackgroundColor' in class_json:
        metadata['base_color'] = class_json['hexBackgroundColor']
    
    # Logo URL (different JSON path per type)
    if 'programLogo' in class_json:
        metadata['logo_url'] = class_json['programLogo'].get('sourceUri', {}).get('uri')
    elif 'logo' in class_json:
        metadata['logo_url'] = class_json['logo'].get('sourceUri', {}).get('uri')
    
    # Hero image URL
    if 'heroImage' in class_json:
        metadata['hero_image_url'] = class_json['heroImage'].get('sourceUri', {}).get('uri')
    
    # Issuer name
    if 'localizedIssuerName' in class_json:
        metadata['issuer_name'] = class_json['localizedIssuerName'].get('defaultValue', {}).get('value')
    elif 'issuerName' in class_json:
        metadata['issuer_name'] = class_json['issuerName']
    
    # ---- Type-specific fields ----
    # Generic
    if 'header' in class_json:
        metadata['header_text'] = class_json['header'].get('defaultValue', {}).get('value')
    if 'cardTitle' in class_json:
        metadata['card_title'] = class_json['cardTitle'].get('defaultValue', {}).get('value')
    
    # EventTicket
    if 'eventName' in class_json:
        metadata['event_name'] = class_json['eventName'].get('defaultValue', {}).get('value')
    if 'venue' in class_json:
        venue = class_json['venue']
        if isinstance(venue, dict):
            metadata['venue_name'] = venue.get('name', {}).get('defaultValue', {}).get('value')
            metadata['venue_address'] = venue.get('address', {}).get('defaultValue', {}).get('value')
    if 'dateTime' in class_json:
        metadata['event_start'] = class_json['dateTime'].get('start')
    
    # Loyalty
    if 'localizedProgramName' in class_json:
        metadata['program_name'] = class_json['localizedProgramName'].get('defaultValue', {}).get('value')
    elif 'programName' in class_json:
        metadata['program_name'] = class_json['programName'].get('defaultValue', {}).get('value') if isinstance(class_json['programName'], dict) else class_json['programName']
    
    # Transit
    if 'transitType' in class_json:
        metadata['transit_type'] = class_json['transitType']
    if 'transitOperatorName' in class_json:
        tn = class_json['transitOperatorName']
        metadata['transit_operator_name'] = tn.get('defaultValue', {}).get('value') if isinstance(tn, dict) else tn
        
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
