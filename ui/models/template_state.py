"""
Template State Management
Manages the state of pass templates during creation/editing
"""

class TemplateState:
    """Manages template data and notifies listeners of changes"""
    
    def __init__(self):
        self.data = {
            "class_id": "",
            "class_type": "Generic",
            "issuer_name": "Your Business",
            "header": "Business Name",
            "card_title": "Pass Title",
            "background_color": "#4285f4",
            "logo_url": None,
            "hero_url": None,
            "fields": []
        }
        self.listeners = []
    
    def subscribe(self, callback):
        """Subscribe to state changes"""
        self.listeners.append(callback)
    
    def unsubscribe(self, callback):
        """Unsubscribe from state changes"""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def update(self, key, value):
        """Update a single field and notify listeners"""
        self.data[key] = value
        self._notify()
    
    def update_multiple(self, updates):
        """Update multiple fields at once"""
        self.data.update(updates)
        self._notify()
    
    def get(self, key, default=None):
        """Get a value from state"""
        return self.data.get(key, default)
    
    def get_all(self):
        """Get all state data"""
        return self.data.copy()
    
    def reset(self):
        """Reset to default state"""
        self.data = {
            "class_id": "",
            "class_type": "Generic",
            "issuer_name": "Your Business",
            "header": "Business Name",
            "card_title": "Pass Title",
            "background_color": "#4285f4",
            "logo_url": None,
            "hero_url": None,
            "fields": []
        }
        self._notify()
    
    def load_from_dict(self, data):
        """Load state from dictionary"""
        self.data.update(data)
        self._notify()
    
    def _notify(self):
        """Notify all listeners of state change"""
        for callback in self.listeners:
            callback(self.data)
