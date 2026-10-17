"""
Attendance Service Layer.
Executes the live face recognition pipeline, makes authoritative attendance decisions,
enforces duplicate prevention, and provides report queries and safe CSV export.
"""

import io
import csv
import base64
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import cv2
import numpy as np

from ..repositories.student_repository import BaseStudentRepository
from ..repositories.attendance_repository import BaseAttendanceRepository
from .face_detector import FaceDetector
from .face_recognizer import FaceRecognizer
from ..utils.validators import sanitize_csv_cell

class AttendanceService:
    def __init__(
        self,
        attendance_repo: BaseAttendanceRepository,
        student_repo: BaseStudentRepository,
        detector: FaceDetector,
        recognizer: FaceRecognizer,
        timezone_str: str = "Asia/Kolkata"
    ):
        self.attendance_repo = attendance_repo
        self.student_repo = student_repo
        self.detector = detector
        self.recognizer = recognizer
        self.timezone_str = timezone_str

    def _get_current_date(self) -> str:
        try:
            tz = ZoneInfo(self.timezone_str)
        except Exception:
            tz = timezone.utc
        return datetime.now(tz).strftime("%Y-%m-%d")

    def decode_base64_image(self, b64_str: str) -> np.ndarray | None:
        try:
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]
            img_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def identify_and_mark(
        self,
        image_b64: str,
        session_id: str = "default",
        mark_attendance: bool = True,
        actor_uid: str = "system"
    ) -> dict:
        """
        Authoritative backend attendance recognition pipeline:
        1. Decode camera frame
        2. Detect faces (YuNet)
        3. Reject if 0 or >1 faces
        4. Extract SFace 128-D embedding
        5. Match against enrolled biometric templates
        6. Reject if similarity < threshold or ambiguous
        7. If valid match & mark_attendance is True, record attendance idempotently
        """
        img_bgr = self.decode_base64_image(image_b64)
        if img_bgr is None:
            return {
                "result": "INVALID_IMAGE",
                "message": "Failed to decode camera frame image."
            }

        faces = self.detector.detect_faces(img_bgr)
        if len(faces) == 0:
            return {
                "result": "NO_FACE_DETECTED",
                "message": "No face detected in the camera frame."
            }

        if len(faces) > 1:
            return {
                "result": "MULTIPLE_FACES",
                "message": f"Multiple faces ({len(faces)}) detected. Attendance requires one subject at a time."
            }

        face = faces[0]
        # Extract feature vector
        try:
            query_vec = self.recognizer.extract_feature(img_bgr, face["_raw_face"])
        except Exception as e:
            return {
                "result": "EXTRACTION_FAILED",
                "message": f"Feature extraction failed: {str(e)}"
            }

        # Retrieve all enrolled active student templates
        enrolled = self.student_repo.get_all_enrolled_templates()
        if not enrolled:
            return {
                "result": "NO_ENROLLED_STUDENTS",
                "message": "No enrolled student face templates in the database."
            }

        # Run identification with threshold and ambiguity check
        match_result = self.recognizer.identify(query_vec, enrolled)

        status = match_result["status"]
        if status == "UNKNOWN_FACE":
            return {
                "result": "UNKNOWN_FACE",
                "message": "Face not recognized. Similarity is below configured threshold.",
                "similarity_score": match_result["similarity_score"],
                "candidates": match_result["candidates"],
                "bbox": face["bbox"]
            }

        if status == "AMBIGUOUS_MATCH":
            return {
                "result": "AMBIGUOUS_MATCH",
                "review_required": True,
                "message": match_result.get("message", "Ambiguous match between multiple candidates."),
                "similarity_score": match_result["similarity_score"],
                "confidence_margin": match_result["confidence_margin"],
                "candidates": match_result["candidates"],
                "bbox": face["bbox"]
            }

        if status != "MATCH":
            return {
                "result": "NOT_RECOGNIZED",
                "message": "Face identification could not determine a confident match."
            }

        # Valid Match Found!
        student = match_result["matched_student"]
        student_id = student["student_id"]
        today_date = self._get_current_date()

        attendance_record = None
        attendance_status = "unrecorded"

        if mark_attendance:
            success, att_status, record = self.attendance_repo.mark_attendance(
                student_id=student_id,
                attendance_date=today_date,
                session_id=session_id,
                method="face_recognition",
                actor_uid=actor_uid,
                status="present",
                tz_name=self.timezone_str
            )
            attendance_status = att_status
            attendance_record = record

        return {
            "result": "SUCCESS",
            "attendance_status": attendance_status,  # 'marked' or 'already_marked'
            "student": student,
            "similarity_score": match_result["similarity_score"],
            "confidence_margin": match_result["confidence_margin"],
            "bbox": face["bbox"],
            "attendance_record": attendance_record
        }

    def mark_manual(
        self,
        student_id: str,
        date: str,
        session_id: str,
        status: str,
        actor_uid: str,
        notes: str = ""
    ) -> dict:
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return {
                "success": False,
                "error_code": "STUDENT_NOT_FOUND",
                "message": f"Student '{student_id}' does not exist."
            }

        success, att_status, record = self.attendance_repo.mark_attendance(
            student_id=student_id,
            attendance_date=date,
            session_id=session_id,
            method="manual",
            actor_uid=actor_uid,
            status=status,
            tz_name=self.timezone_str,
            notes=notes
        )

        return {
            "success": success,
            "attendance_status": att_status,
            "record": record
        }

    def get_attendance_records(
        self,
        student_id: str = None,
        date: str = None,
        start_date: str = None,
        end_date: str = None,
        session_id: str = None,
        department: str = None,
        status: str = None
    ) -> list[dict]:
        records = self.attendance_repo.get_attendance(
            student_id=student_id,
            date=date,
            start_date=start_date,
            end_date=end_date,
            session_id=session_id,
            status=status
        )

        # Enrich records with student profile metadata
        enriched = []
        student_cache = {}
        for rec in records:
            sid = rec["student_id"]
            if sid not in student_cache:
                s = self.student_repo.get_by_id(sid)
                student_cache[sid] = s

            s_info = student_cache.get(sid) or {}
            rec_dept = s_info.get("department", "Unknown")

            if department and rec_dept != department:
                continue

            rec_copy = dict(rec)
            rec_copy["full_name"] = s_info.get("full_name", sid)
            rec_copy["department"] = rec_dept
            rec_copy["year_of_study"] = s_info.get("year_of_study", "-")
            enriched.append(rec_copy)

        return enriched

    def get_dashboard_metrics(self) -> dict:
        all_students = self.student_repo.list_students()
        active_students = [s for s in all_students if s.get("status") == "active"]
        total_active = len(active_students)

        today_date = self._get_current_date()
        today_summary = self.attendance_repo.get_today_summary(today_date, total_active)

        # Recent 10 checkins today
        recent_records = self.get_attendance_records(date=today_date)[:10]

        # 7-day trend calculation
        today_dt = datetime.strptime(today_date, "%Y-%m-%d")
        trend = []
        for i in range(6, -1, -1):
            day_dt = today_dt - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            recs = self.attendance_repo.get_attendance(date=day_str)
            present_cnt = len(recs)
            pct = round((present_cnt / total_active * 100), 1) if total_active > 0 else 0.0
            trend.append({
                "date": day_str,
                "day_label": day_dt.strftime("%a"),
                "present": present_cnt,
                "percentage": pct
            })

        return {
            "summary": today_summary,
            "recent_check_ins": recent_records,
            "trend": trend,
            "enrolled_faces_count": sum(1 for s in all_students if s.get("has_face_enrolled"))
        }

    def generate_csv_export(
        self,
        date: str = None,
        start_date: str = None,
        end_date: str = None,
        department: str = None,
        student_id: str = None
    ) -> str:
        """
        Generates CSV report with formula injection escaping.
        """
        records = self.get_attendance_records(
            student_id=student_id,
            date=date,
            start_date=start_date,
            end_date=end_date,
            department=department
        )

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow([
            "Attendance ID",
            "Student ID",
            "Student Name",
            "Department",
            "Year",
            "Date",
            "Check-In Time",
            "Status",
            "Method",
            "Session",
            "Created By",
            "Notes"
        ])

        for r in records:
            writer.writerow([
                sanitize_csv_cell(r.get("attendance_id")),
                sanitize_csv_cell(r.get("student_id")),
                sanitize_csv_cell(r.get("full_name")),
                sanitize_csv_cell(r.get("department")),
                sanitize_csv_cell(r.get("year_of_study")),
                sanitize_csv_cell(r.get("attendance_date")),
                sanitize_csv_cell(r.get("check_in_time")),
                sanitize_csv_cell(r.get("status")),
                sanitize_csv_cell(r.get("method")),
                sanitize_csv_cell(r.get("session_id")),
                sanitize_csv_cell(r.get("created_by")),
                sanitize_csv_cell(r.get("notes", ""))
            ])

        return output.getvalue()
