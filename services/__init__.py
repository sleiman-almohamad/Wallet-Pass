"""
Service Layer for Wallet Passes Application
Provides domain services for business logic operations
"""

from .class_update_service import propagate_class_update_to_passes

__all__ = ['propagate_class_update_to_passes']
