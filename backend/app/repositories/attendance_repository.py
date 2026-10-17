"""
Attendance Repository Layer.
Handles atomic, idempotent attendance recording, duplicate prevention via deterministic document IDs,
and multi-criteria attendance queries.
"""

import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from abc import ABC, abstractmethod

class BaseAttendanceRepository(ABC):
    @abstractmethod
    def mark_attendance(
        self,
        student_id: str,
        attendance_date: str,
        session_id: str,
        method: str,
        actor_uid: str,
        status: str = "present",
        tz_name: str = "Asia/Kolkata",
        notes: str = ""
    ) -> tuple[bool, str, dict]:
        """
        Marks attendance idempotently.
        Returns: (success, result_status, attendance_record)
        result_status is 'marked' or 'already_marked'
        """
        pass

    @abstractmethod
    def get_attendance(
        self,
        student_id: str = None,
        date: str = None,
        start_date: str = None,
        end_date: str = None,
        session_id: str = None,
        status: str = None
    ) -> list[dict]:
        pass

    @abstractmethod
    def get_today_summary(self, today_date: str, total_active_students: int) -> dict:
        pass


class InMemoryAttendanceRepository(BaseAttendanceRepository):
    """Thread-safe in-memory attendance repository."""
    def __init__(self):
        self.records = {}  # key: attendance_id -> record
        self.lock = threading.Lock()
        self.audit_logs = []

    def _get_tz_time(self, tz_name: str):
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        now = datetime.now(tz)
        return now.strftime("%H:%M:%S"), now.isoformat()

    def mark_attendance(
        self,
        student_id: str,
        attendance_date: str,
        session_id: str = "default",
        method: str = "face_recognition",
        actor_uid: str = "system",
        status: str = "present",
        tz_name: str = "Asia/Kolkata",
        notes: str = ""
    ) -> tuple[bool, str, dict]:
        sid = student_id.upper()
        sess = session_id.strip() if session_id else "default"
        doc_id = f"att_{sid}_{attendance_date}_{sess}"

        with self.lock:
            if doc_id in self.records:
                # Already marked today for this session
                return True, "already_marked", dict(self.records[doc_id])

            check_in_time, now_iso = self._get_tz_time(tz_name)
            record = {
                "attendance_id": doc_id,
                "student_id": sid,
                "attendance_date": attendance_date,
                "check_in_time": check_in_time,
                "status": status,
                "method": method,
                "session_id": sess,
                "created_at": now_iso,
                "created_by": actor_uid,
                "notes": notes
            }
            self.records[doc_id] = record

            self.audit_logs.append({
                "actor_uid": actor_uid,
                "action": "ATTENDANCE_MARKED",
                "target_type": "attendance",
                "target_id": doc_id,
                "method": method,
                "timestamp": now_iso
            })

            return True, "marked", dict(record)

    def get_attendance(
        self,
        student_id: str = None,
        date: str = None,
        start_date: str = None,
        end_date: str = None,
        session_id: str = None,
        status: str = None
    ) -> list[dict]:
        with self.lock:
            results = []
            for rec in self.records.values():
                if student_id and rec.get("student_id") != student_id.upper():
                    continue
                if session_id and rec.get("session_id") != session_id:
                    continue
                if status and rec.get("status") != status:
                    continue
                if date and rec.get("attendance_date") != date:
                    continue
                if start_date and rec.get("attendance_date") < start_date:
                    continue
                if end_date and rec.get("attendance_date") > end_date:
                    continue

                results.append(dict(rec))

            results.sort(key=lambda x: (x.get("attendance_date", ""), x.get("check_in_time", "")), reverse=True)
            return results

    def get_today_summary(self, today_date: str, total_active_students: int) -> dict:
        today_records = self.get_attendance(date=today_date)
        present_count = len(today_records)
        not_marked_count = max(0, total_active_students - present_count)
        rate = round((present_count / total_active_students * 100), 1) if total_active_students > 0 else 0.0

        return {
            "date": today_date,
            "total_active_students": total_active_students,
            "present_today": present_count,
            "not_marked_today": not_marked_count,
            "attendance_rate_percent": rate
        }


class FirestoreAttendanceRepository(BaseAttendanceRepository):
    """Production Firestore attendance repository with atomic operations."""
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("attendance")
        self.audit_collection = db.collection("audit_logs")

    def _get_tz_time(self, tz_name: str):
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        now = datetime.now(tz)
        return now.strftime("%H:%M:%S"), now.isoformat()

    def mark_attendance(
        self,
        student_id: str,
        attendance_date: str,
        session_id: str = "default",
        method: str = "face_recognition",
        actor_uid: str = "system",
        status: str = "present",
        tz_name: str = "Asia/Kolkata",
        notes: str = ""
    ) -> tuple[bool, str, dict]:
        sid = student_id.upper()
        sess = session_id.strip() if session_id else "default"
        doc_id = f"att_{sid}_{attendance_date}_{sess}"
        doc_ref = self.collection.document(doc_id)

        # Check existing record first for fast idempotency
        existing = doc_ref.get()
        if existing.exists:
            return True, "already_marked", existing.to_dict()

        check_in_time, now_iso = self._get_tz_time(tz_name)
        record = {
            "attendance_id": doc_id,
            "student_id": sid,
            "attendance_date": attendance_date,
            "check_in_time": check_in_time,
            "status": status,
            "method": method,
            "session_id": sess,
            "created_at": now_iso,
            "created_by": actor_uid,
            "notes": notes
        }

        try:
            # Using create() ensures atomicity: fails if doc already exists concurrently
            doc_ref.create(record)
        except Exception as e:
            # Check if another process created it concurrently
            existing = doc_ref.get()
            if existing.exists:
                return True, "already_marked", existing.to_dict()
            raise e

        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "ATTENDANCE_MARKED",
            "target_type": "attendance",
            "target_id": doc_id,
            "method": method,
            "timestamp": now_iso
        })

        return True, "marked", record

    def get_attendance(
        self,
        student_id: str = None,
        date: str = None,
        start_date: str = None,
        end_date: str = None,
        session_id: str = None,
        status: str = None
    ) -> list[dict]:
        query = self.collection
        if student_id:
            query = query.where("student_id", "==", student_id.upper())
        if date:
            query = query.where("attendance_date", "==", date)
        if start_date:
            query = query.where("attendance_date", ">=", start_date)
        if end_date:
            query = query.where("attendance_date", "<=", end_date)
        if session_id:
            query = query.where("session_id", "==", session_id)
        if status:
            query = query.where("status", "==", status)

        docs = query.stream()
        results = [doc.to_dict() for doc in docs]
        results.sort(key=lambda x: (x.get("attendance_date", ""), x.get("check_in_time", "")), reverse=True)
        return results

    def get_today_summary(self, today_date: str, total_active_students: int) -> dict:
        today_records = self.get_attendance(date=today_date)
        present_count = len(today_records)
        not_marked_count = max(0, total_active_students - present_count)
        rate = round((present_count / total_active_students * 100), 1) if total_active_students > 0 else 0.0

        return {
            "date": today_date,
            "total_active_students": total_active_students,
            "present_today": present_count,
            "not_marked_today": not_marked_count,
            "attendance_rate_percent": rate
        }
