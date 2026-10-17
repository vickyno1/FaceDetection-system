"""
Health and System Status Route.
Public endpoint for liveness probes, model diagnostics, and deployment verification.
"""

from datetime import datetime, timezone
from flask import Blueprint, current_app
from ..utils.responses import success_response
from ..extensions import face_detector, face_recognizer

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def health_check():
    yunet_ok = face_detector is not None and face_detector.detector is not None
    sface_ok = face_recognizer is not None and face_recognizer.recognizer is not None
    mock_mode = current_app.config.get("MOCK_FIREBASE", True)

    status_data = {
        "status": "healthy" if (yunet_ok and sface_ok) else "degraded",
        "service": "student-attendance-face-recognition",
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "configured_timezone": current_app.config.get("ATTENDANCE_TIMEZONE", "Asia/Kolkata"),
        "database_backend": "in-memory (mock)" if mock_mode else "cloud-firestore",
        "models": {
            "yunet_detector_loaded": yunet_ok,
            "sface_recognizer_loaded": sface_ok,
            "similarity_threshold": current_app.config.get("FACE_SIMILARITY_THRESHOLD"),
            "match_margin": current_app.config.get("FACE_MATCH_MARGIN")
        }
    }

    status_code = 200 if (yunet_ok and sface_ok) else 200
    return success_response(
        data=status_data,
        message="System health probe successful.",
        status_code=status_code
    )
