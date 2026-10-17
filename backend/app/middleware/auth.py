"""
Authentication and Authorization Middleware.
Verifies Firebase ID Tokens server-side and enforces administrator roles.
"""

from functools import wraps
from flask import request, current_app
from ..utils.responses import error_response

def require_auth(require_admin=True):
    """
    Decorator to protect API routes with Firebase ID token verification.
    Extracts Bearer token from the Authorization header and verifies it.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization", None)
            if not auth_header:
                return error_response(
                    message="Missing Authorization header.",
                    error_code="UNAUTHORIZED",
                    status_code=401
                )

            parts = auth_header.split(" ")
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return error_response(
                    message="Invalid Authorization header format. Expected 'Bearer <token>'.",
                    error_code="UNAUTHORIZED",
                    status_code=401
                )

            token = parts[1].strip()

            # Handle Mock / Testing mode
            if current_app.config.get("MOCK_FIREBASE", False) or current_app.config.get("TESTING", False):
                if token in ("mock-admin-token", "test-token", "demo-token"):
                    request.user = {
                        "uid": "admin-mock-uid-001",
                        "email": "admin@attendance.college.edu",
                        "role": "admin",
                        "name": "System Administrator (Demo)"
                    }
                    return f(*args, **kwargs)
                elif token.startswith("user-token"):
                    if require_admin:
                        return error_response(
                            message="Administrator privileges required.",
                            error_code="FORBIDDEN",
                            status_code=403
                        )
                    request.user = {
                        "uid": "student-mock-uid-999",
                        "email": "student@attendance.college.edu",
                        "role": "student"
                    }
                    return f(*args, **kwargs)
                else:
                    return error_response(
                        message="Invalid or expired authentication token.",
                        error_code="INVALID_TOKEN",
                        status_code=401
                    )

            # Live Firebase Admin verification
            try:
                import firebase_admin.auth as fb_auth
                decoded_token = fb_auth.verify_id_token(token, check_revoked=True)
                uid = decoded_token.get("uid")
                email = decoded_token.get("email", "")
                
                # Check custom claims or admin role
                is_admin = decoded_token.get("admin", False) or decoded_token.get("role") == "admin"
                
                # If specific admin list or claims are used
                if require_admin and not is_admin:
                    # Check fallback: if this is the designated bootstrap admin email
                    admin_email = current_app.config.get("BOOTSTRAP_ADMIN_EMAIL", "admin@attendance.edu")
                    if email and email.lower() == admin_email.lower():
                        is_admin = True
                    else:
                        return error_response(
                            message="Administrator privileges required.",
                            error_code="FORBIDDEN",
                            status_code=403
                        )

                request.user = {
                    "uid": uid,
                    "email": email,
                    "role": "admin" if is_admin else "user",
                    "claims": decoded_token
                }
                return f(*args, **kwargs)

            except fb_auth.RevokedIdTokenError:
                return error_response(
                    message="Token has been revoked.",
                    error_code="TOKEN_REVOKED",
                    status_code=401
                )
            except fb_auth.ExpiredIdTokenError:
                return error_response(
                    message="Authentication token has expired.",
                    error_code="TOKEN_EXPIRED",
                    status_code=401
                )
            except Exception as e:
                # Do not leak internal exception details to client
                current_app.logger.warning(f"Firebase token verification failed: {str(e)}")
                return error_response(
                    message="Invalid authentication credentials.",
                    error_code="INVALID_TOKEN",
                    status_code=401
                )

        return decorated_function
    return decorator
