"""
Standardized API Response Helpers.
Ensures consistent JSON responses, error codes, and prevents leakage of internal traces.
"""

from flask import jsonify

def success_response(data=None, message="Success", status_code=200, meta=None):
    """Formats a successful JSON response."""
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code

def error_response(message="An error occurred", error_code="BAD_REQUEST", status_code=400, details=None):
    """Formats a standardized error JSON response."""
    payload = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status_code
