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
        'header': None,
        'subheader': None,
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
        # Generic text module rows (our DB stores these as 3-column rows)
        'text_module_rows': [],
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
        metadata['header'] = class_json['header'].get('defaultValue', {}).get('value')
    if 'cardTitle' in class_json:
        metadata['card_title'] = class_json['cardTitle'].get('defaultValue', {}).get('value')

    # Generic: textModulesData and linksModuleData -> our row-based storage
    # Google uses a flat list; our UI/DB expects rows with left/middle/right columns.
    # Common IDs created by our app: row_{row_index}_{left|middle|right}
    text_modules = class_json.get("textModulesData") or []
    link_uris = class_json.get("linksModuleData", {}).get("uris") or []
    
    # Combine both into a unified list to process
    all_modules = []
    for mod in text_modules:
        if isinstance(mod, dict):
            mod_copy = dict(mod)
            mod_copy["_type"] = "text"
            all_modules.append(mod_copy)
            
    for mod in link_uris:
        if isinstance(mod, dict):
            mod_copy = dict(mod)
            mod_copy["_type"] = "link"
            mod_copy["header"] = mod.get("description", "")
            mod_copy["body"] = mod.get("uri", "")
            all_modules.append(mod_copy)

    if all_modules:
        rows_by_idx = {}
        fallback_row = 0

        for mod in all_modules:
            mid = mod.get("id") or ""
            header = mod.get("header")
            body = mod.get("body")
            m_type = mod.get("_type", "text")

            # defaults
            row_index = None
            col = None

            if isinstance(mid, str) and mid.startswith("row_"):
                # expected: row_0_left, row_1_middle, row_2_right
                parts = mid.split("_")
                if len(parts) >= 3:
                    try:
                        row_index = int(parts[1])
                        col = parts[2]
                    except Exception:
                        row_index = None
                        col = None

            if row_index is None:
                row_index = fallback_row
                col = "left"
                fallback_row += 1

            if col not in ("left", "middle", "right"):
                col = "left"

            row = rows_by_idx.setdefault(row_index, {"row_index": row_index})
            row[f"{col}_header"] = header
            row[f"{col}_body"] = body
            row[f"{col}_type"] = m_type

        metadata["text_module_rows"] = [rows_by_idx[k] for k in sorted(rows_by_idx.keys())]
    
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
