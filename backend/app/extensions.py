"""
Extensions and Service Container.
Manages database initialization, computer vision models, and service injection.
"""

import os
from pathlib import Path
from flask import current_app

from .config import Config
from .services.face_detector import FaceDetector
from .services.face_recognizer import FaceRecognizer
from .repositories.student_repository import InMemoryStudentRepository, FirestoreStudentRepository
from .repositories.attendance_repository import InMemoryAttendanceRepository, FirestoreAttendanceRepository
from .services.student_service import StudentService
from .services.attendance_service import AttendanceService

# Singletons
face_detector = None
face_recognizer = None
student_repository = None
attendance_repository = None
student_service = None
attendance_service = None

def init_app(app):
    global face_detector, face_recognizer, student_repository, attendance_repository, student_service, attendance_service

    yunet_path = app.config.get("YUNET_MODEL_PATH")
    sface_path = app.config.get("SFACE_MODEL_PATH")
    conf_thresh = app.config.get("FACE_DETECTION_CONFIDENCE", 0.80)
    sim_thresh = app.config.get("FACE_SIMILARITY_THRESHOLD", 0.380)
    margin = app.config.get("FACE_MATCH_MARGIN", 0.080)

    # Auto-download models if missing (e.g. freshly cloned repository)
    if not (yunet_path and Path(yunet_path).exists() and sface_path and Path(sface_path).exists()):
        try:
            from ..models.download_models import download_models
            model_dir = str(app.config.get("MODEL_DIR", Path(__file__).resolve().parent.parent / "models"))
            app.logger.info(f"Pretrained ONNX models missing. Auto-downloading into {model_dir}...")
            download_models(model_dir)
        except Exception as e:
            app.logger.warning(f"Could not auto-download models: {e}. Run 'python backend/models/download_models.py' manually.")

    # Initialize Face Detection & Recognition
    try:
        face_detector = FaceDetector(model_path=str(yunet_path), conf_threshold=conf_thresh)
        app.logger.info("FaceDetector (YuNet) initialized successfully.")
    except Exception as e:
        app.logger.warning(f"FaceDetector initialized with warning/offline mode: {e}")
        face_detector = FaceDetector(model_path=None)

    try:
        face_recognizer = FaceRecognizer(model_path=str(sface_path), threshold=sim_thresh, match_margin=margin)
        app.logger.info("FaceRecognizer (SFace) initialized successfully.")
    except Exception as e:
        app.logger.warning(f"FaceRecognizer initialized with warning/offline mode: {e}")
        face_recognizer = FaceRecognizer(model_path=None, threshold=sim_thresh, match_margin=margin)

    # Initialize Repositories (Firestore or In-Memory)
    use_mock = app.config.get("MOCK_FIREBASE", True) or app.config.get("TESTING", False)

    if not use_mock:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            cred_path = app.config.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and Path(cred_path).exists():
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

            db = firestore.client()
            student_repository = FirestoreStudentRepository(db)
            attendance_repository = FirestoreAttendanceRepository(db)
            app.logger.info("Initialized Google Cloud Firestore repositories via Firebase Admin SDK.")
        except Exception as e:
            app.logger.error(f"Failed to connect to Firebase Firestore: {e}. Falling back to In-Memory repository for safety.")
            student_repository = InMemoryStudentRepository()
            attendance_repository = InMemoryAttendanceRepository()
    else:
        app.logger.info("Initialized InMemory repositories (Mock / Testing mode enabled).")
        student_repository = InMemoryStudentRepository()
        attendance_repository = InMemoryAttendanceRepository()

    # Initialize Services
    student_service = StudentService(
        student_repo=student_repository,
        detector=face_detector,
        recognizer=face_recognizer
    )

    attendance_service = AttendanceService(
        attendance_repo=attendance_repository,
        student_repo=student_repository,
        detector=face_detector,
        recognizer=face_recognizer,
        timezone_str=app.config.get("ATTENDANCE_TIMEZONE", "Asia/Kolkata")
    )
