"""
Application Entry Point.
Runs the Flask development server or serves via WSGI.
"""

import sys
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    print("=" * 70)
    print("  Student Attendance Management System - Backend Server")
    print("=" * 70)
    print(f"  * Environment     : {Config.FLASK_ENV}")
    print(f"  * Database Mode   : {'In-Memory (Mock)' if Config.MOCK_FIREBASE else 'Cloud Firestore'}")
    print(f"  * Timezone        : {Config.ATTENDANCE_TIMEZONE}")
    print(f"  * YuNet Path      : {Config.YUNET_MODEL_PATH}")
    print(f"  * SFace Path      : {Config.SFACE_MODEL_PATH}")
    print(f"  * Match Threshold : {Config.FACE_SIMILARITY_THRESHOLD}")
    print(f"  * Match Margin    : {Config.FACE_MATCH_MARGIN}")
    print(f"  * Listening on    : http://{Config.HOST}:{Config.PORT}")
    print("=" * 70)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )
