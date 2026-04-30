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
        """Generic template.
        
        Maps text_module_rows from the local DB into Google's cardTemplateOverride
        so that object-level textModulesData (with specific IDs) can be displayed
        on the front of the pass.
        """
        template = {
            "id": class_id,
        }

        # Add branding to the Class so it reflects in the Google Wallet Console
        bg_color = kwargs.get("background_color")
        if bg_color:
            template["hexBackgroundColor"] = bg_color if bg_color.startswith("#") else f"#{bg_color}"

        logo_url = kwargs.get("logo_url") or kwargs.get("program_logo_url")
        if logo_url:
            template["logo"] = {
                "sourceUri": {"uri": str(logo_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Logo"}}
            }

        hero_url = kwargs.get("hero_image_url")
        if hero_url:
            template["heroImage"] = {
                "sourceUri": {"uri": str(hero_url)},
                "contentDescription": {"defaultValue": {"language": "en-US", "value": "Hero Image"}}
            }

        card_title = kwargs.get("card_title")
        if card_title:
            template["cardTitle"] = {"defaultValue": {"language": "en-US", "value": str(card_title)}}

        header_text = kwargs.get("header_text")
        if header_text:
            template["header"] = {"defaultValue": {"language": "en-US", "value": str(header_text)}}

        issuer_name = kwargs.get("issuer_name")
        if issuer_name:
            template["issuerName"] = str(issuer_name)

        text_module_rows = kwargs.get("text_module_rows", [])
        
        # Build class-level textModulesData and linksModuleData for default values.
        # Also build a lookup map from module ID → link array index so we can
        # reference links by numeric index in detailsTemplateOverride field paths.
        # Google Wallet requires numeric indexing for linksModuleData
        # (e.g. "object.linksModuleData[0]"), unlike textModulesData which
        # supports string ID lookups (e.g. "object.textModulesData['myId']").
        class_text_modules = []
        class_link_modules = []
        link_id_to_index = {}  # e.g. {"row_4_left": 0, "row_5_left": 1, ...}
        for r_idx, row in enumerate(text_module_rows):
            for pos in ["left", "middle", "right"]:
                hdr = row.get(f"{pos}_header")
                bdy = row.get(f"{pos}_body")
                m_type = row.get(f"{pos}_type", "text")
                if hdr or bdy:
                    m_id = f"row_{r_idx}_{pos}"
                    if m_type == "link":
                        if not bdy or not str(bdy).strip():
                            continue
                        uri = str(bdy).strip() if str(bdy).strip().startswith(("http://", "https://", "mailto:", "tel:")) else f"https://{str(bdy).strip()}"
                        link_mod = {"uri": uri}
                        if hdr: link_mod["description"] = hdr
                        if m_id: link_mod["id"] = m_id
                        link_id_to_index[m_id] = len(class_link_modules)
                        class_link_modules.append(link_mod)
                    else:
                        class_text_modules.append({
                            "id": m_id,
                            "header": hdr or "",
                            "body": str(bdy).strip() if bdy else ""
                        })
        template["textModulesData"] = class_text_modules
        template["linksModuleData"] = {"uris": class_link_modules}
        if text_module_rows:
            card_row_template_infos = []
            # Only the first 2 rows are shown on the front of the pass.
            # Remaining text modules still exist in textModulesData on the
            # object level and Google automatically renders them on the
            # back / details view.
            front_rows = text_module_rows[:2]
            for i, row in enumerate(front_rows):
                row_items = []
                
                # Check which items are present in the blueprint
                if row.get("left_header") or row.get("left_body"):
                    row_items.append({
                        "firstValue": {
                            "fields": [{"fieldPath": f"object.textModulesData['row_{i}_left']"}]
                        }
                    })
                
                if row.get("middle_header") or row.get("middle_body"):
                    row_items.append({
                        "firstValue": {
                            "fields": [{"fieldPath": f"object.textModulesData['row_{i}_middle']"}]
                        }
                    })
                
                if row.get("right_header") or row.get("right_body"):
                    row_items.append({
                        "firstValue": {
                            "fields": [{"fieldPath": f"object.textModulesData['row_{i}_right']"}]
                        }
                    })

                if not row_items:
                    continue

                # Determine layout based on number of items
                row_template = {}
                if len(row_items) == 1:
                    row_template = {"oneItem": {"item": row_items[0]}}
                elif len(row_items) == 2:
                    row_template = {
                        "twoItems": {
                            "startItem": row_items[0],
                            "endItem": row_items[1]
                        }
                    }
                elif len(row_items) >= 3:
                    row_template = {
                        "threeItems": {
                            "startItem": row_items[0],
                            "middleItem": row_items[1],
                            "endItem": row_items[2]
                        }
                    }
                
                card_row_template_infos.append(row_template)

            if card_row_template_infos:
                # Build detailsTemplateOverride to exclude front rows from the back
                back_rows = text_module_rows[2:]
                details_infos = []
                for j, back_row in enumerate(back_rows):
                    actual_row_idx = back_row.get("row_index", j + 2)
                    for pos in ["left", "middle", "right"]:
                        if back_row.get(f"{pos}_header") or back_row.get(f"{pos}_body"):
                            m_type = back_row.get(f"{pos}_type", "text")
                            m_id = f"row_{actual_row_idx}_{pos}"
                            if m_type == "link":
                                 fields_list = [
                                     {"fieldPath": f"class.linksModuleData.uris['{m_id}']"},
                                     {"fieldPath": f"object.linksModuleData.uris['{m_id}']"}
                                 ]
                            else:
                                 fields_list = [{"fieldPath": f"object.textModulesData['{m_id}']"}]
                                 
                            details_infos.append({
                                "item": {
                                    "firstValue": {
                                        "fields": fields_list
                                    }
                                }
                            })
                
                # Append standard items that should always appear on the back
                # since detailsTemplateOverride hides everything not explicitly listed.
                details_infos.append({
                    "item": {
                        "firstValue": {
                            "fields": [{"fieldPath": "object.textModulesData['description']"}]
                        }
                    }
                })
                details_infos.append({
                    "item": {
                        "firstValue": {
                            "fields": [{"fieldPath": "object.infoModulesData['generic_info_module']"}]
                        }
                    }
                })
                
                # Add the dedicated notification message to the back of the pass
                details_infos.append({
                    "item": {
                        "firstValue": {
                            "fields": [{"fieldPath": "object.textModulesData['notification_message']"}]
                        }
                    }
                })
                
                class_template_info = {
                    "cardTemplateOverride": {
                        "cardRowTemplateInfos": card_row_template_infos
                    }
                }
                # Only add detailsTemplateOverride if there are back items or if we
                # need to hide the front rows (empty details = nothing on back)
                class_template_info["detailsTemplateOverride"] = {
                    "detailsItemInfos": details_infos
                }
                template["classTemplateInfo"] = class_template_info

        return template
    
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
                "label": "label.background_color",
                "type": "color",
                "hint": "#4285f4"
            }
        }
        
        if class_type == "LoyaltyCard":
            return {
                **common_fields,
                "localizedIssuerName.defaultValue.value": {
                    "label": "label.issuer_name",
                    "type": "text",
                    "hint": "Your Business Name"
                },
                "localizedProgramName.defaultValue.value": {
                    "label": "label.program_name",
                    "type": "text",
                    "hint": "Loyalty Program"
                },
                "programLogo.sourceUri.uri": {
                    "label": "label.program_logo_url",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "label.hero_image_url",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg"
                }
            }
        elif class_type == "GiftCard":
            return {
                **common_fields,
                "localizedIssuerName.defaultValue.value": {
                    "label": "label.issuer_name",
                    "type": "text",
                    "hint": "Your Business Name"
                },
                "programLogo.sourceUri.uri": {
                    "label": "label.card_logo_url",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "label.hero_image_url",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg"
                }
            }
        elif class_type == "EventTicket":
            return {
                **common_fields,
                "issuerName": {
                    "label": "label.issuer_name",
                    "type": "text",
                    "hint": "Your Business"
                },
                "eventName.defaultValue.value": {
                    "label": "label.event_name",
                    "type": "text",
                    "hint": "Event Name"
                },
                "venue.name.defaultValue.value": {
                    "label": "label.venue_name",
                    "type": "text",
                    "hint": "Venue Name"
                },
                "venue.address.defaultValue.value": {
                    "label": "label.venue_address",
                    "type": "text",
                    "hint": "123 Main St, City"
                },
                "dateTime.start": {
                    "label": "label.event_start_time",
                    "type": "datetime",
                    "hint": "2025-12-31T19:00:00"
                },
                "logo.sourceUri.uri": {
                    "label": "label.logo_url",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "label.hero_image_url",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg (1032x336px recommended)"
                }
            }
        elif class_type == "TransitPass":
            return {
                **common_fields,
                "issuerName": {
                    "label": "label.issuer_name",
                    "type": "text",
                    "hint": "Transit Authority"
                },
                "transitType": {
                    "label": "label.transit_type",
                    "type": "select",
                    "hint": "TRANSIT_TYPE_BUS",
                    "options": ["TRANSIT_TYPE_BUS", "TRANSIT_TYPE_RAIL", "TRANSIT_TYPE_TRAM", "TRANSIT_TYPE_FERRY"]
                },
                "logo.sourceUri.uri": {
                    "label": "label.logo_url",
                    "type": "url",
                    "hint": "https://example.com/logo.png"
                },
                "heroImage.sourceUri.uri": {
                    "label": "label.hero_image_url",
                    "type": "url",
                    "hint": "https://example.com/hero.jpg (1032x336px recommended)"
                }
            }
        else:  # Generic — rules-only (branding is per-pass)
            return {}


# Helper functions for easy template access
def get_template(class_type: str, class_id: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to get a template"""
    return JSONTemplateManager.get_template(class_type, class_id, **kwargs)


def get_editable_fields(class_type: str) -> Dict[str, Dict[str, str]]:
    """Convenience function to get editable fields for a class type"""
    return JSONTemplateManager.get_editable_fields(class_type)
