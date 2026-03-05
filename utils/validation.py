"""
Input validation helpers, shared across views.
"""

import configs


def ensure_issuer_prefix(value: str) -> str:
    """Ensure an ID string has the issuer-ID prefix."""
    if value and not value.startswith(configs.ISSUER_ID):
        return f"{configs.ISSUER_ID}.{value}"
    return value


def strip_issuer_prefix(value: str) -> str:
    """Remove the issuer-ID prefix from an ID string."""
    prefix = f"{configs.ISSUER_ID}."
    if value and value.startswith(prefix):
        return value[len(prefix):]
    return value
