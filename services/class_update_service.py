"""
Class Update Service
Handles propagation of class/template updates to all affected pass objects
"""

import logging
from typing import Dict, Any, List
from database.db_manager import DatabaseManager
from wallet_service import WalletClient

# Configure logging
logger = logging.getLogger(__name__)


def propagate_class_update_to_passes(
    class_id: str,
    updated_class: Dict[str, Any],
    db_manager: DatabaseManager,
    wallet_client: WalletClient
) -> Dict[str, Any]:
    """
    Propagate class updates to all associated pass objects in Google Wallet
    
    This function is the core domain service that orchestrates updating all
    pass objects when a class template is modified. It ensures end users
    receive push notifications about the changes.
    
    Args:
        class_id: The class identifier (local, without issuer prefix)
        updated_class: Dictionary containing updated class data including:
            - class_type: Type of pass (EventTicket, LoyaltyCard, Generic)
            - class_json: Complete Google Wallet class JSON
            - Other metadata fields
        db_manager: DatabaseManager instance for data access
        wallet_client: WalletClient instance for Google Wallet API calls
    
    Returns:
        Dictionary with update summary:
        {
            "updated_count": int,      # Successfully updated passes
            "failed_count": int,       # Failed updates
            "total_count": int,        # Total passes found
            "errors": List[str]        # Error messages for failures
        }
    """
    logger.info(f"Starting pass propagation for class: {class_id}")
    
    # Initialize result counters
    result = {
        "updated_count": 0,
        "failed_count": 0,
        "total_count": 0,
        "errors": []
    }
    
    try:
        # Fetch all passes for this class
        passes = db_manager.get_passes_by_class(class_id)
        result["total_count"] = len(passes)

        # region agent log
        try:
            import json as _json, time as _time
            with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                _ts = int(_time.time() * 1000)
                _f.write(_json.dumps({
                    "id": f"log_{_ts}",
                    "timestamp": _ts,
                    "location": "services/class_update_service.py:propagate_class_update_to_passes:passes_fetched",
                    "message": "Fetched passes for class",
                    "data": {"class_id": class_id, "total_passes": len(passes)},
                    "runId": "initial",
                    "hypothesisId": "H2"
                }) + "\n")
        except Exception:
            pass
        # endregion
        
        if not passes:
            logger.info(f"No passes found for class {class_id}, nothing to update")
            return result
        
        logger.info(f"Found {len(passes)} passes to update for class {class_id}")
        
        # Extract class type for pass object updates
        class_type = updated_class.get('class_type', 'EventTicket')
        
        # Update each pass object in Google Wallet
        for pass_obj in passes:
            object_id = pass_obj.get('object_id')
            
            try:
                # Build the full object ID with issuer prefix if needed
                full_object_id = wallet_client._prepare_ids_to_try(object_id)[0]
                full_class_id = wallet_client._prepare_ids_to_try(class_id)[0]
                
                # Extract pass-specific data
                holder_name = pass_obj.get('holder_name', '')
                holder_email = pass_obj.get('holder_email', '')
                pass_data = pass_obj.get('pass_data', {})

                # region agent log
                try:
                    import json as _json, time as _time
                    with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                        _ts = int(_time.time() * 1000)
                        _f.write(_json.dumps({
                            "id": f"log_{_ts}",
                            "timestamp": _ts,
                            "location": "services/class_update_service.py:propagate_class_update_to_passes:before_update_pass",
                            "message": "About to call wallet_client.update_pass_object",
                            "data": {
                                "class_id": class_id,
                                "object_id": object_id,
                                "holder_email": holder_email
                            },
                            "runId": "initial",
                            "hypothesisId": "H3"
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                
                # Update the pass object in Google Wallet
                logger.debug(f"Updating pass object: {full_object_id}")
                wallet_client.update_pass_object(
                    object_id=full_object_id,
                    class_id=full_class_id,
                    holder_name=holder_name,
                    holder_email=holder_email,
                    pass_data=pass_data,
                    class_type=class_type
                )
                
                # Log success to database
                db_manager.create_notification(
                    class_id=class_id,
                    object_id=object_id,
                    status="Sent",
                    message="Pass updated successfully via Google Wallet API"
                )

                # region agent log
                try:
                    import json as _json, time as _time
                    with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                        _ts = int(_time.time() * 1000)
                        _f.write(_json.dumps({
                            "id": f"log_{_ts}",
                            "timestamp": _ts,
                            "location": "services/class_update_service.py:propagate_class_update_to_passes:after_update_pass",
                            "message": "Successfully updated pass in Google Wallet",
                            "data": {
                                "class_id": class_id,
                                "object_id": object_id
                            },
                            "runId": "initial",
                            "hypothesisId": "H3"
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                
                result["updated_count"] += 1
                logger.debug(f"Successfully updated pass: {object_id}")
                
            except Exception as e:
                result["failed_count"] += 1
                error_msg = f"Failed to update pass {object_id}: {str(e)}"
                result["errors"].append(error_msg)
                
                # Log failure to database
                db_manager.create_notification(
                    class_id=class_id,
                    object_id=object_id,
                    status="Failed",
                    message=str(e)
                )

                # region agent log
                try:
                    import json as _json, time as _time
                    with open("/home/slimanutd/sleiman/B2F/Projects/WalletPasses/.cursor/debug.log", "a") as _f:
                        _ts = int(_time.time() * 1000)
                        _f.write(_json.dumps({
                            "id": f"log_{_ts}",
                            "timestamp": _ts,
                            "location": "services/class_update_service.py:propagate_class_update_to_passes:on_error",
                            "message": "Error while updating pass in Google Wallet",
                            "data": {
                                "class_id": class_id,
                                "object_id": object_id,
                                "error": str(e)
                            },
                            "runId": "initial",
                            "hypothesisId": "H3"
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                
                logger.error(error_msg, exc_info=True)
                # Continue with other passes (best-effort)
        
        logger.info(
            f"Pass propagation completed for class {class_id}: "
            f"{result['updated_count']}/{result['total_count']} successful, "
            f"{result['failed_count']} failed"
        )
        
    except Exception as e:
        error_msg = f"Critical error during pass propagation: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg, exc_info=True)
    
    return result
