"""
Application Configuration Module.
Loads environment variables and validates configuration parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root if present
backend_root = Path(__file__).resolve().parent.parent
dotenv_path = backend_root / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Config:
    """Base application configuration."""
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Server host & port
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # CORS
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Timezone
    ATTENDANCE_TIMEZONE = os.getenv("ATTENDANCE_TIMEZONE", "Asia/Kolkata")

    # Firebase
    MOCK_FIREBASE = os.getenv("MOCK_FIREBASE", "true").lower() in ("true", "1", "yes")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Face Recognition Models and Calibration
    BASE_DIR = backend_root
    _model_dir_env = os.getenv("FACE_MODEL_DIR", "models")
    if os.path.isabs(_model_dir_env):
        MODEL_DIR = Path(_model_dir_env)
    else:
        MODEL_DIR = BASE_DIR / _model_dir_env

    YUNET_MODEL_PATH = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
    SFACE_MODEL_PATH = MODEL_DIR / "face_recognition_sface_2021dec.onnx"

    # Calibration parameters
    FACE_SIMILARITY_THRESHOLD = float(os.getenv("FACE_SIMILARITY_THRESHOLD", "0.380"))
    FACE_MATCH_MARGIN = float(os.getenv("FACE_MATCH_MARGIN", "0.080"))
    FACE_MIN_SIZE = int(os.getenv("FACE_MIN_SIZE", "60"))
    FACE_DETECTION_CONFIDENCE = float(os.getenv("FACE_DETECTION_CONFIDENCE", "0.80"))
    FACE_MIN_BLUR_SCORE = float(os.getenv("FACE_MIN_BLUR_SCORE", "50.0"))

    @classmethod
    def validate(cls):
        """Validates critical configuration parameters at startup."""
        errors = []
        if not (0.0 < cls.FACE_SIMILARITY_THRESHOLD < 1.0):
            errors.append(f"FACE_SIMILARITY_THRESHOLD must be between 0 and 1, got {cls.FACE_SIMILARITY_THRESHOLD}")
        if not (0.0 <= cls.FACE_MATCH_MARGIN < 0.5):
            errors.append(f"FACE_MATCH_MARGIN must be between 0 and 0.5, got {cls.FACE_MATCH_MARGIN}")
        
        if not cls.MOCK_FIREBASE:
            if not cls.GOOGLE_APPLICATION_CREDENTIALS and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                errors.append("GOOGLE_APPLICATION_CREDENTIALS must be set when MOCK_FIREBASE is false.")
            elif cls.GOOGLE_APPLICATION_CREDENTIALS and not Path(cls.GOOGLE_APPLICATION_CREDENTIALS).exists():
                errors.append(f"Credentials file not found at: {cls.GOOGLE_APPLICATION_CREDENTIALS}")

        return errors

class TestConfig(Config):
    """Test configuration override."""
    TESTING = True
    DEBUG = False
    MOCK_FIREBASE = True
    SECRET_KEY = "test-secret-key"
