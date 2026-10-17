"""
Attendance Reporting and Manual Administration Routes.
Provides dashboard statistics, filtered attendance queries, manual marking, and CSV export.
"""

from datetime import datetime
from flask import Blueprint, request, Response
from ..middleware.auth import require_auth
from ..utils.responses import success_response, error_response
from ..utils.validators import validate_date_str, validate_student_id
from ..extensions import attendance_service

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api")

@attendance_bp.route("/dashboard", methods=["GET"])
@require_auth(require_admin=True)
def get_dashboard():
    data = attendance_service.get_dashboard_metrics()
    return success_response(data=data, message="Dashboard metrics retrieved.")

@attendance_bp.route("/attendance", methods=["GET"])
@require_auth(require_admin=True)
def list_attendance():
    date = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    dept = request.args.get("department")
    student_id = request.args.get("student_id")
    status = request.args.get("status")
    session_id = request.args.get("session_id")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    if date:
        val_ok, res = validate_date_str(date)
        if not val_ok:
            return error_response(message=f"Invalid date: {res}", error_code="INVALID_DATE", status_code=400)
        date = res

    if start_date:
        val_ok, res = validate_date_str(start_date)
        if not val_ok:
            return error_response(message=f"Invalid start_date: {res}", error_code="INVALID_DATE", status_code=400)
        start_date = res

    if end_date:
        val_ok, res = validate_date_str(end_date)
        if not val_ok:
            return error_response(message=f"Invalid end_date: {res}", error_code="INVALID_DATE", status_code=400)
        end_date = res

    records = attendance_service.get_attendance_records(
        student_id=student_id,
        date=date,
        start_date=start_date,
        end_date=end_date,
        session_id=session_id,
        department=dept,
        status=status
    )

    total = len(records)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated = records[start_idx:end_idx]

    return success_response(
        data=paginated,
        message="Attendance records retrieved.",
        meta={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    )

@attendance_bp.route("/attendance/mark-manual", methods=["POST"])
@require_auth(require_admin=True)
def mark_manual_attendance():
    payload = request.get_json(silent=True) or {}
    student_id = payload.get("student_id")
    date = payload.get("date")
    status = payload.get("status", "present").strip().lower()
    session_id = payload.get("session_id", "default")
    notes = payload.get("notes", "Manual administrative override")

    valid_id, clean_id = validate_student_id(student_id)
    if not valid_id:
        return error_response(message=clean_id, error_code="INVALID_ID", status_code=400)

    val_date, clean_date = validate_date_str(date)
    if not val_date:
        return error_response(message=clean_date, error_code="INVALID_DATE", status_code=400)

    if status not in ("present", "absent", "late"):
        return error_response(
            message="Status must be one of: present, absent, late.",
            error_code="INVALID_STATUS",
            status_code=400
        )

    actor_uid = getattr(request, "user", {}).get("uid", "admin")
    result = attendance_service.mark_manual(
        student_id=clean_id,
        date=clean_date,
        session_id=session_id,
        status=status,
        actor_uid=actor_uid,
        notes=notes
    )

    if not result.get("success"):
        return error_response(
            message=result.get("message", "Failed to mark attendance manually."),
            error_code=result.get("error_code", "ATTENDANCE_ERROR"),
            status_code=400
        )

    return success_response(
        data=result,
        message=f"Manual attendance recorded for student '{clean_id}'."
    )

@attendance_bp.route("/attendance/summary", methods=["GET"])
@require_auth(require_admin=True)
def get_attendance_summary():
    date = request.args.get("date")
    if date:
        val_ok, res = validate_date_str(date)
        if not val_ok:
            return error_response(message=res, error_code="INVALID_DATE", status_code=400)
        date = res
    else:
        date = attendance_service._get_current_date()

    all_students = attendance_service.student_repo.list_students()
    active_students = [s for s in all_students if s.get("status") == "active"]
    summary = attendance_service.attendance_repo.get_today_summary(date, len(active_students))
    return success_response(data=summary, message="Attendance summary retrieved.")

@attendance_bp.route("/attendance/export", methods=["GET"])
@require_auth(require_admin=True)
def export_attendance_csv():
    date = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    dept = request.args.get("department")
    student_id = request.args.get("student_id")

    if date:
        val_ok, res = validate_date_str(date)
        if not val_ok:
            return error_response(message=res, error_code="INVALID_DATE", status_code=400)
        date = res

    if start_date:
        val_ok, res = validate_date_str(start_date)
        if not val_ok:
            return error_response(message=res, error_code="INVALID_DATE", status_code=400)
        start_date = res

    if end_date:
        val_ok, res = validate_date_str(end_date)
        if not val_ok:
            return error_response(message=res, error_code="INVALID_DATE", status_code=400)
        end_date = res

    csv_data = attendance_service.generate_csv_export(
        date=date,
        start_date=start_date,
        end_date=end_date,
        department=dept,
        student_id=student_id
    )

    filename = f"attendance_report_{date or (start_date + '_to_' + end_date if start_date and end_date else 'all')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )
