"""
Google Wallet State Management
Sub-states for Manage Templates and Manage Passes tabs.
"""


class _ObservableState:
    """Base class providing the observer pattern."""

    def __init__(self, defaults: dict):
        self._data: dict = dict(defaults)
        self._listeners: list = []

    # -- observer API --
    def subscribe(self, callback):
        self._listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        for cb in self._listeners:
            cb(self._data)

    # -- data access --
    def get(self, key, default=None):
        return self._data.get(key, default)

    def get_all(self) -> dict:
        return self._data.copy()

    def update(self, key, value):
        self._data[key] = value
        self._notify()

    def update_multiple(self, updates: dict):
        self._data.update(updates)
        self._notify()

    def set_status(self, message: str, color: str = "green"):
        self._data["status_message"] = message
        self._data["status_color"] = color
        self._notify()

    def reset(self):
        raise NotImplementedError


# ──────────────────────────────────────────────
# Manage Templates state
# ──────────────────────────────────────────────
_TEMPLATE_DEFAULTS = {
    "classes_list": [],
    "selected_class_id": None,
    "current_json": {},
    "class_type": None,
    "notification_message": "",
    "status_message": "",
    "status_color": "grey",
    "is_loading": False,
}


class ManageTemplateState(_ObservableState):
    """State for the *Manage Templates* tab."""

    def __init__(self):
        super().__init__(_TEMPLATE_DEFAULTS)

    def reset(self):
        self._data = dict(_TEMPLATE_DEFAULTS)
        self._notify()


# ──────────────────────────────────────────────
# Manage Passes state
# ──────────────────────────────────────────────
_PASS_DEFAULTS = {
    "classes_list": [],
    "selected_class_id": None,
    "passes_list": [],
    "selected_pass_id": None,
    "current_json": {},
    "class_type": None,
    "status_message": "",
    "status_color": "grey",
    "is_loading": False,
}


class ManagePassState(_ObservableState):
    """State for the *Manage Passes* tab."""

    def __init__(self):
        super().__init__(_PASS_DEFAULTS)

    def reset(self):
        self._data = dict(_PASS_DEFAULTS)
        self._notify()
