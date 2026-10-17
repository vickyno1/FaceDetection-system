"""
Student Management and Face Enrollment Routes.
Protected endpoints for student registration, profile updates, and biometric enrollment.
"""

from flask import Blueprint, request
from ..middleware.auth import require_auth
from ..utils.responses import success_response, error_response
from ..utils.validators import validate_student_data, validate_student_id
from ..extensions import student_service

students_bp = Blueprint("students", __name__, url_prefix="/api/students")

@students_bp.route("", methods=["GET"])
@require_auth(require_admin=True)
def list_students():
    dept = request.args.get("department")
    status = request.args.get("status")
    search = request.args.get("q")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    students = student_service.list_students(department=dept, status=status, search=search)
    total = len(students)

    # Simple pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated = students[start_idx:end_idx]

    return success_response(
        data=paginated,
        message="Students retrieved successfully.",
        meta={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    )

@students_bp.route("", methods=["POST"])
@require_auth(require_admin=True)
def create_student():
    data = request.get_json(silent=True) or {}
    is_valid, sanitized, errors = validate_student_data(data, is_update=False)
    if not is_valid:
        return error_response(
            message="Student validation failed.",
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=errors
        )

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    try:
        student = student_service.create_student(sanitized, actor_uid=actor_uid)
        return success_response(
            data=student,
            message="Student created successfully.",
            status_code=201
        )
    except ValueError as ve:
        return error_response(
            message=str(ve),
            error_code="DUPLICATE_STUDENT_ID",
            status_code=409
        )
    except Exception as e:
        return error_response(
            message=f"Failed to create student: {str(e)}",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500
        )

@students_bp.route("/<student_id>", methods=["GET"])
@require_auth(require_admin=True)
def get_student(student_id):
    valid, clean_id = validate_student_id(student_id)
    if not valid:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    student = student_service.get_student(clean_id)
    if not student:
        return error_response(
            message=f"Student with ID '{clean_id}' not found.",
            error_code="NOT_FOUND",
            status_code=404
        )
    return success_response(data=student, message="Student profile retrieved.")

@students_bp.route("/<student_id>", methods=["PUT"])
@require_auth(require_admin=True)
def update_student(student_id):
    valid, clean_id = validate_student_id(student_id)
    if not valid:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    data = request.get_json(silent=True) or {}
    is_valid, sanitized, errors = validate_student_data(data, is_update=True)
    if not is_valid:
        return error_response(
            message="Student update validation failed.",
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=errors
        )

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    updated = student_service.update_student(clean_id, sanitized, actor_uid=actor_uid)
    if not updated:
        return error_response(
            message=f"Student with ID '{clean_id}' not found.",
            error_code="NOT_FOUND",
            status_code=404
        )

    return success_response(data=updated, message="Student updated successfully.")

@students_bp.route("/<student_id>", methods=["DELETE"])
@require_auth(require_admin=True)
def delete_student(student_id):
    valid, clean_id = validate_student_id(student_id)
    if not valid:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    success = student_service.deactivate_student(clean_id, actor_uid=actor_uid)
    if not success:
        return error_response(
            message=f"Student with ID '{clean_id}' not found.",
            error_code="NOT_FOUND",
            status_code=404
        )

    return success_response(
        data={"student_id": clean_id, "status": "inactive"},
        message=f"Student '{clean_id}' has been deactivated."
    )

@students_bp.route("/<student_id>/enroll-face", methods=["POST"])
@require_auth(require_admin=True)
def enroll_face(student_id):
    valid, clean_id = validate_student_id(student_id)
    if not valid:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    payload = request.get_json(silent=True) or {}
    images = payload.get("images", [])
    consent = payload.get("consent", False)

    if not consent:
        return error_response(
            message="Biometric enrollment cannot proceed without explicit consent.",
            error_code="CONSENT_REQUIRED",
            status_code=400
        )

    if not images or not isinstance(images, list):
        return error_response(
            message="An array of captured image frames (base64) is required.",
            error_code="BAD_REQUEST",
            status_code=400
        )

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    enroll_result = student_service.enroll_face(
        student_id=clean_id,
        image_b64_list=images,
        consent=consent,
        actor_uid=actor_uid
    )

    if not enroll_result.get("success"):
        return error_response(
            message=enroll_result.get("message", "Enrollment failed."),
            error_code=enroll_result.get("error_code", "ENROLLMENT_FAILED"),
            status_code=422,
            details=enroll_result.get("diagnostics")
        )

    return success_response(
        data=enroll_result,
        message=f"Face template enrolled successfully for student '{clean_id}'."
    )

@students_bp.route("/<student_id>/face-template", methods=["DELETE"])
@require_auth(require_admin=True)
def delete_face_template(student_id):
    valid, clean_id = validate_student_id(student_id)
    if not valid:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    success = student_service.delete_face_template(clean_id, actor_uid=actor_uid)
    if not success:
        return error_response(
            message=f"Student with ID '{clean_id}' not found.",
            error_code="NOT_FOUND",
            status_code=404
        )

    return success_response(
        data={"student_id": clean_id, "has_face_enrolled": False},
        message=f"Biometric face template deleted for student '{clean_id}'."
    )
