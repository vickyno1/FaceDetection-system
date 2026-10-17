"""
Flask Application Factory.
Configures CORS, registers blueprints, initializes extensions, and handles errors.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config
from .extensions import init_app
from .utils.responses import error_response

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Restrict max request size (16MB to comfortably allow multi-frame webcam uploads)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # Validate configuration
    config_errors = config_class.validate()
    if config_errors:
        for err in config_errors:
            app.logger.warning(f"Config Warning: {err}")

    # Configure CORS
    allowed_origin = app.config.get("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(
        app,
        resources={r"/api/*": {"origins": [allowed_origin, "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"]
    )

    # Initialize extensions and service singletons
    init_app(app)

    # Register blueprints
    from .routes.health import health_bp
    from .routes.students import students_bp
    from .routes.recognition import recognition_bp
    from .routes.attendance import attendance_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(attendance_bp)

    # Global Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        return error_response(message="Bad Request.", error_code="BAD_REQUEST", status_code=400)

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response(message="The requested endpoint does not exist.", error_code="NOT_FOUND", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response(message="HTTP method not allowed for this route.", error_code="METHOD_NOT_ALLOWED", status_code=405)

    @app.errorhandler(413)
    def handle_payload_too_large(e):
        return error_response(message="Upload payload exceeds maximum limit of 16MB.", error_code="PAYLOAD_TOO_LARGE", status_code=413)

    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f"Internal server error: {e}")
        return error_response(message="An internal server error occurred.", error_code="INTERNAL_SERVER_ERROR", status_code=500)

    return app
