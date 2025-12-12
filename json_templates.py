"""
JSON Template Manager for Google Wallet Pass Classes
Provides templates for different class types with customizable fields
"""

from typing import Dict, Any, Optional
import configs


class JSONTemplateManager:
    """Manages JSON templates for different Google Wallet pass class types"""
    
    @staticmethod
    def get_template(class_type: str, class_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get a JSON template for a specific class type
        
        Args:
            class_type: Type of pass ('LoyaltyCard', 'GiftCard', 'EventTicket', 'Generic', 'TransitPass')
            class_id: The class identifier (without issuer prefix)
            **kwargs: Optional fields to customize the template
        
        Returns:
            Dictionary with Google Wallet class JSON structure
        """
        # Ensure class_id has issuer prefix
        full_class_id = class_id if '.' in class_id else f"{configs.ISSUER_ID}.{class_id}"
        
        # Get template based on type
        if class_type == "LoyaltyCard":
            return JSONTemplateManager._loyalty_card_template(full_class_id, **kwargs)
        elif class_type == "GiftCard":
            return JSONTemplateManager._gift_card_template(full_class_id, **kwargs)
        elif class_type == "EventTicket":
            return JSONTemplateManager._event_ticket_template(full_class_id, **kwargs)
        elif class_type == "TransitPass":
            return JSONTemplateManager._transit_pass_template(full_class_id, **kwargs)
        else:  # Generic
            return JSONTemplateManager._generic_template(full_class_id, **kwargs)
    
    @staticmethod
    def _loyalty_card_template(class_id: str, **kwargs) -> Dict[str, Any]:
        """LoyaltyCard template"""
        return {
            "id": class_id,
            "programLogo": {
                "sourceUri": {
                    "uri": kwargs.get("program_logo_url", "https://images.unsplash.com/photo-1512568400610-62da28bc8a13?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=660&h=660")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("logo_description", "Program Logo")
                    }
                }
            },
            "localizedIssuerName": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("issuer_name", "[TEST ONLY] Your Business")
                }
            },
            "localizedProgramName": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("program_name", "Loyalty Program")
                }
            },
            "hexBackgroundColor": kwargs.get("background_color", "#72461d"),
            "heroImage": {
                "sourceUri": {
                    "uri": kwargs.get("hero_image_url", "https://images.unsplash.com/photo-1447933601403-0c6688de566e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1032&h=336")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("hero_description", "Hero Image")
                    }
                }
            },
            "reviewStatus": "UNDER_REVIEW"
        }
    
    @staticmethod
    def _gift_card_template(class_id: str, **kwargs) -> Dict[str, Any]:
        """GiftCard template"""
        return {
            "id": class_id,
            "programLogo": {
                "sourceUri": {
                    "uri": kwargs.get("program_logo_url", "https://images.unsplash.com/photo-1513151233558-d860c5398176?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=660&h=660")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("logo_description", "Gift Card Logo")
                    }
                }
            },
            "localizedIssuerName": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("issuer_name", "[TEST ONLY] Your Business")
                }
            },
            "hexBackgroundColor": kwargs.get("background_color", "#358b1d"),
            "heroImage": {
                "sourceUri": {
                    "uri": kwargs.get("hero_image_url", "https://images.unsplash.com/photo-1513151233558-d860c5398176?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1032&h=336")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("hero_description", "Hero Image")
                    }
                }
            },
            "reviewStatus": "UNDER_REVIEW"
        }
    
    @staticmethod
    def _event_ticket_template(class_id: str, **kwargs) -> Dict[str, Any]:
        """EventTicket template"""
        return {
            "id": class_id,
            "issuerName": kwargs.get("issuer_name", "Your Business"),
            "eventName": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("event_name", "Event Name")
                }
            },
            "venue": {
                "name": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("venue_name", "Venue Name")
                    }
                },
                "address": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("venue_address", "123 Main St, City")
                    }
                }
            },
            "dateTime": {
                "start": kwargs.get("event_start", "2025-12-31T19:00:00")
            },
            "logo": {
                "sourceUri": {
                    "uri": kwargs.get("logo_url", "https://images.unsplash.com/photo-1512568400610-62da28bc8a13?ixlib=rb-4.0.3&auto=format&fit=crop&w=660&h=660")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("logo_description", "Event Logo")
                    }
                }
            },
            "hexBackgroundColor": kwargs.get("background_color", "#4285f4"),
            "heroImage": {
                "sourceUri": {
                    "uri": kwargs.get("hero_image_url", "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?ixlib=rb-4.0.3&auto=format&fit=crop&w=1032&h=336")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("hero_description", "Event Hero")
                    }
                }
            },
            "reviewStatus": "UNDER_REVIEW"
        }
    
    @staticmethod
    def _transit_pass_template(class_id: str, **kwargs) -> Dict[str, Any]:
        """TransitPass template"""
        return {
            "id": class_id,
            "issuerName": kwargs.get("issuer_name", "Transit Authority"),
            "transitType": kwargs.get("transit_type", "TRANSIT_TYPE_BUS"),
            "logo": {
                "sourceUri": {
                    "uri": kwargs.get("logo_url", "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=660&h=660")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("logo_description", "Transit Logo")
                    }
                }
            },
            "hexBackgroundColor": kwargs.get("background_color", "#1a73e8"),
            "heroImage": {
                "sourceUri": {
                    "uri": kwargs.get("hero_image_url", "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1032&h=336")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("hero_description", "Transit Hero")
                    }
                }
            },
            "reviewStatus": "UNDER_REVIEW"
        }
    
    @staticmethod
    def _generic_template(class_id: str, **kwargs) -> Dict[str, Any]:
        """Generic template"""
        return {
            "id": class_id,
            "issuerName": kwargs.get("issuer_name", "Your Business"),
            "header": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("header_text", "Business Name")
                }
            },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": kwargs.get("card_title", "Pass Title")
                }
            },
            "logo": {
                "sourceUri": {
                    "uri": kwargs.get("logo_url", "https://images.unsplash.com/photo-1512568400610-62da28bc8a13?auto=format&fit=crop&w=660&h=660")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("logo_description", "Logo")
                    }
                }
            },
            "hexBackgroundColor": kwargs.get("background_color", "#4285f4"),
            "heroImage": {
                "sourceUri": {
                    "uri": kwargs.get("hero_image_url", "https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=1032&h=336")
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": kwargs.get("hero_description", "Hero Image")
                    }
                }
            },
            "reviewStatus": "UNDER_REVIEW"
        }
    
    @staticmethod
    def get_editable_fields(class_type: str) -> Dict[str, Dict[str, str]]:
        """
        Get a mapping of editable fields for a given class type
        
        Returns:
            Dictionary mapping JSON paths to field metadata
            Format: {
                "json_path": {
                    "label": "Field Label",
                    "type": "text|color|url|datetime",
                    "hint": "Placeholder text"
                }
            }
        """
        common_fields = {
            "hexBackgroundColor": {
                "label": "Background Color",
                "type": "color",
                "hint": "#4285f4"
            }
        }
        
        if class_type == "LoyaltyCard":
            return {
                **common_fields,
                "localizedIssuerName.defaultValue.value": {
                    "label": "Issuer Name",
                    "type": "text",
                    "hint": "Your Business Name"
                },
                "localizedProgramName.defaultValue.value": {
                    "label": "Program Name",
                    "type": "text",
                    "hint": "Loyalty Program"
                },
                "programLogo.sourceUri.uri": {
                    "label": "Program Logo URL",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "Hero Image URL",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg"
                }
            }
        elif class_type == "GiftCard":
            return {
                **common_fields,
                "localizedIssuerName.defaultValue.value": {
                    "label": "Issuer Name",
                    "type": "text",
                    "hint": "Your Business Name"
                },
                "programLogo.sourceUri.uri": {
                    "label": "Card Logo URL",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "Hero Image URL",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg"
                }
            }
        elif class_type == "EventTicket":
            return {
                **common_fields,
                "issuerName": {
                    "label": "Issuer Name",
                    "type": "text",
                    "hint": "Your Business"
                },
                "eventName.defaultValue.value": {
                    "label": "Event Name",
                    "type": "text",
                    "hint": "Event Name"
                },
                "venue.name.defaultValue.value": {
                    "label": "Venue Name",
                    "type": "text",
                    "hint": "Venue Name"
                },
                "venue.address.defaultValue.value": {
                    "label": "Venue Address",
                    "type": "text",
                    "hint": "123 Main St, City"
                },
                "dateTime.start": {
                    "label": "Event Start Time",
                    "type": "datetime",
                    "hint": "2025-12-31T19:00:00"
                },
                "logo.sourceUri.uri": {
                    "label": "Logo URL",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "Hero Image URL",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg (1032x336px recommended)"
                }
            }
        elif class_type == "TransitPass":
            return {
                **common_fields,
                "issuerName": {
                    "label": "Issuer Name",
                    "type": "text",
                    "hint": "Transit Authority"
                },
                "transitType": {
                    "label": "Transit Type",
                    "type": "select",
                    "hint": "TRANSIT_TYPE_BUS",
                    "options": ["TRANSIT_TYPE_BUS", "TRANSIT_TYPE_RAIL", "TRANSIT_TYPE_TRAM", "TRANSIT_TYPE_FERRY"]
                },
                "logo.sourceUri.uri": {
                    "label": "Logo URL",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "Hero Image URL",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg (1032x336px recommended)"
                }
            }
        else:  # Generic
            return {
                **common_fields,
                "issuerName": {
                    "label": "Issuer Name",
                    "type": "text",
                    "hint": "Your Business"
                },
                "header.defaultValue.value": {
                    "label": "Header Text",
                    "type": "text",
                    "hint": "Business Name"
                },
                "cardTitle.defaultValue.value": {
                    "label": "Card Title",
                    "type": "text",
                    "hint": "Pass Title"
                },
                "logo.sourceUri.uri": {
                    "label": "Logo URL",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "Hero Image URL",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg (1032x336px recommended)"
                }
            }


# Helper functions for easy template access
def get_template(class_type: str, class_id: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to get a template"""
    return JSONTemplateManager.get_template(class_type, class_id, **kwargs)


def get_editable_fields(class_type: str) -> Dict[str, Dict[str, str]]:
    """Convenience function to get editable fields for a class type"""
    return JSONTemplateManager.get_editable_fields(class_type)
