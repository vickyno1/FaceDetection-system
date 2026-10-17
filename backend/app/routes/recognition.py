"""
Face Recognition and Identification Routes.
Handles camera frame recognition, identity resolution, and attendance recording.
"""

from flask import Blueprint, request
from ..middleware.auth import require_auth
from ..utils.responses import success_response, error_response
from ..extensions import attendance_service

recognition_bp = Blueprint("recognition", __name__, url_prefix="/api/recognition")

@recognition_bp.route("/identify", methods=["POST"])
@require_auth(require_admin=False)
def identify_face():
    """
    Submits a webcam capture for face detection, feature extraction,
    matching against enrolled student biometric templates, and atomic attendance marking.
    """
    payload = request.get_json(silent=True) or {}
    image_b64 = payload.get("image")
    if not image_b64:
        return error_response(
            message="No image provided in request body.",
            error_code="BAD_REQUEST",
            status_code=400
        )

    session_id = payload.get("session_id", "default")
    mark_attendance = payload.get("mark_attendance", True)
    actor_uid = getattr(request, "user", {}).get("uid", "terminal")

    result = attendance_service.identify_and_mark(
        image_b64=image_b64,
        session_id=session_id,
        mark_attendance=mark_attendance,
        actor_uid=actor_uid
    )

    result_type = result.get("result")

    # If successful match
    if result_type == "SUCCESS":
        return success_response(
            data=result,
            message="Face identified successfully."
        )

    # Ambiguous match (top 2 candidates too close)
    if result_type == "AMBIGUOUS_MATCH":
        return success_response(
            data=result,
            message="Candidate ambiguity detected. Automatic attendance rejected for safety.",
            status_code=200
        )

    # Unknown face
    if result_type == "UNKNOWN_FACE":
        return success_response(
            data=result,
            message="Unknown face. Match did not meet configured similarity threshold.",
            status_code=200
        )

    # Multiple faces or no face
    if result_type in ("NO_FACE_DETECTED", "MULTIPLE_FACES", "NO_ENROLLED_STUDENTS"):
        return success_response(
            data=result,
            message=result.get("message", "Could not process face."),
            status_code=200
        )

    return error_response(
        message=result.get("message", "Face recognition failed."),
        error_code=result_type or "RECOGNITION_ERROR",
        status_code=422
    )
