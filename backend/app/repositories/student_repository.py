"""
Student Repository Layer.
Handles persistent storage of student profiles, biometric face templates,
and audit logs using Cloud Firestore or an In-Memory store for offline/testing mode.
"""

from datetime import datetime, timezone
from abc import ABC, abstractmethod

class BaseStudentRepository(ABC):
    @abstractmethod
    def get_by_id(self, student_id: str) -> dict | None:
        pass

    @abstractmethod
    def list_students(self, department: str = None, status: str = None, search: str = None) -> list[dict]:
        pass

    @abstractmethod
    def create(self, student_data: dict, actor_uid: str) -> dict:
        pass

    @abstractmethod
    def update(self, student_id: str, update_data: dict, actor_uid: str) -> dict | None:
        pass

    @abstractmethod
    def deactivate(self, student_id: str, actor_uid: str) -> bool:
        pass

    @abstractmethod
    def save_face_template(self, student_id: str, template: list[float], model_version: str, consent: bool, actor_uid: str) -> bool:
        pass

    @abstractmethod
    def delete_face_template(self, student_id: str, actor_uid: str) -> bool:
        pass

    @abstractmethod
    def get_all_enrolled_templates(self) -> list[dict]:
        pass


class InMemoryStudentRepository(BaseStudentRepository):
    """In-memory student repository for testing and offline development."""
    def __init__(self):
        self.students = {}
        self.audit_logs = []

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def get_by_id(self, student_id: str) -> dict | None:
        student = self.students.get(student_id.upper())
        if not student:
            return None
        # Return a copy without exposing internal references
        res = dict(student)
        return res

    def list_students(self, department: str = None, status: str = None, search: str = None) -> list[dict]:
        results = []
        for s in self.students.values():
            if status and s.get("status") != status:
                continue
            if department and s.get("department") != department:
                continue
            if search:
                q = search.lower()
                name_match = q in s.get("full_name", "").lower()
                id_match = q in s.get("student_id", "").lower()
                if not (name_match or id_match):
                    continue

            # Return public view without raw face_template in default lists
            item = dict(s)
            item["has_face_enrolled"] = bool(s.get("face_template"))
            item.pop("face_template", None)
            results.append(item)

        results.sort(key=lambda x: x.get("student_id", ""))
        return results

    def create(self, student_data: dict, actor_uid: str) -> dict:
        sid = student_data["student_id"].upper()
        if sid in self.students:
            raise ValueError(f"Student with ID '{sid}' already exists.")

        now_str = self._now()
        record = {
            "student_id": sid,
            "full_name": student_data["full_name"],
            "department": student_data["department"],
            "year_of_study": student_data["year_of_study"],
            "email": student_data.get("email", ""),
            "status": student_data.get("status", "active"),
            "face_template": None,
            "face_model_version": None,
            "enrollment_consent": False,
            "created_at": now_str,
            "updated_at": now_str
        }
        self.students[sid] = record

        self.audit_logs.append({
            "actor_uid": actor_uid,
            "action": "STUDENT_CREATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": now_str
        })
        return dict(record)

    def update(self, student_id: str, update_data: dict, actor_uid: str) -> dict | None:
        sid = student_id.upper()
        if sid not in self.students:
            return None

        record = self.students[sid]
        for field in ("full_name", "department", "year_of_study", "email", "status"):
            if field in update_data:
                record[field] = update_data[field]
        record["updated_at"] = self._now()

        self.audit_logs.append({
            "actor_uid": actor_uid,
            "action": "STUDENT_UPDATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": record["updated_at"]
        })
        return dict(record)

    def deactivate(self, student_id: str, actor_uid: str) -> bool:
        sid = student_id.upper()
        if sid not in self.students:
            return False
        self.students[sid]["status"] = "inactive"
        self.students[sid]["updated_at"] = self._now()

        self.audit_logs.append({
            "actor_uid": actor_uid,
            "action": "STUDENT_DEACTIVATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": self._now()
        })
        return True

    def save_face_template(self, student_id: str, template: list[float], model_version: str, consent: bool, actor_uid: str) -> bool:
        sid = student_id.upper()
        if sid not in self.students:
            return False

        record = self.students[sid]
        record["face_template"] = list(template)
        record["face_model_version"] = model_version
        record["enrollment_consent"] = consent
        record["updated_at"] = self._now()

        self.audit_logs.append({
            "actor_uid": actor_uid,
            "action": "FACE_TEMPLATE_ENROLLED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": self._now(),
            "model_version": model_version
        })
        return True

    def delete_face_template(self, student_id: str, actor_uid: str) -> bool:
        sid = student_id.upper()
        if sid not in self.students:
            return False

        record = self.students[sid]
        record["face_template"] = None
        record["face_model_version"] = None
        record["enrollment_consent"] = False
        record["updated_at"] = self._now()

        self.audit_logs.append({
            "actor_uid": actor_uid,
            "action": "FACE_TEMPLATE_DELETED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": self._now()
        })
        return True

    def get_all_enrolled_templates(self) -> list[dict]:
        templates = []
        for s in self.students.values():
            if s.get("status") == "active" and s.get("face_template") and s.get("enrollment_consent"):
                templates.append({
                    "student_id": s["student_id"],
                    "full_name": s["full_name"],
                    "department": s["department"],
                    "face_template": s["face_template"]
                })
        return templates


class FirestoreStudentRepository(BaseStudentRepository):
    """Production Firestore student repository using Firebase Admin SDK."""
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("students")
        self.audit_collection = db.collection("audit_logs")

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def get_by_id(self, student_id: str) -> dict | None:
        doc = self.collection.document(student_id.upper()).get()
        if not doc.exists:
            return None
        return doc.to_dict()

    def list_students(self, department: str = None, status: str = None, search: str = None) -> list[dict]:
        query = self.collection
        if status:
            query = query.where("status", "==", status)
        if department:
            query = query.where("department", "==", department)

        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if search:
                q = search.lower()
                if q not in data.get("full_name", "").lower() and q not in data.get("student_id", "").lower():
                    continue
            item = dict(data)
            item["has_face_enrolled"] = bool(data.get("face_template"))
            item.pop("face_template", None)
            results.append(item)

        results.sort(key=lambda x: x.get("student_id", ""))
        return results

    def create(self, student_data: dict, actor_uid: str) -> dict:
        sid = student_data["student_id"].upper()
        doc_ref = self.collection.document(sid)
        if doc_ref.get().exists:
            raise ValueError(f"Student with ID '{sid}' already exists.")

        now_str = self._now()
        record = {
            "student_id": sid,
            "full_name": student_data["full_name"],
            "department": student_data["department"],
            "year_of_study": student_data["year_of_study"],
            "email": student_data.get("email", ""),
            "status": student_data.get("status", "active"),
            "face_template": None,
            "face_model_version": None,
            "enrollment_consent": False,
            "created_at": now_str,
            "updated_at": now_str
        }
        doc_ref.set(record)

        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "STUDENT_CREATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": now_str
        })
        return record

    def update(self, student_id: str, update_data: dict, actor_uid: str) -> dict | None:
        sid = student_id.upper()
        doc_ref = self.collection.document(sid)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        update_payload = {}
        for field in ("full_name", "department", "year_of_study", "email", "status"):
            if field in update_data:
                update_payload[field] = update_data[field]
        update_payload["updated_at"] = self._now()

        doc_ref.update(update_payload)
        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "STUDENT_UPDATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": update_payload["updated_at"]
        })
        return doc_ref.get().to_dict()

    def deactivate(self, student_id: str, actor_uid: str) -> bool:
        sid = student_id.upper()
        doc_ref = self.collection.document(sid)
        if not doc_ref.get().exists:
            return False

        now_str = self._now()
        doc_ref.update({"status": "inactive", "updated_at": now_str})
        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "STUDENT_DEACTIVATED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": now_str
        })
        return True

    def save_face_template(self, student_id: str, template: list[float], model_version: str, consent: bool, actor_uid: str) -> bool:
        sid = student_id.upper()
        doc_ref = self.collection.document(sid)
        if not doc_ref.get().exists:
            return False

        now_str = self._now()
        doc_ref.update({
            "face_template": list(template),
            "face_model_version": model_version,
            "enrollment_consent": consent,
            "updated_at": now_str
        })
        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "FACE_TEMPLATE_ENROLLED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": now_str,
            "model_version": model_version
        })
        return True

    def delete_face_template(self, student_id: str, actor_uid: str) -> bool:
        sid = student_id.upper()
        doc_ref = self.collection.document(sid)
        if not doc_ref.get().exists:
            return False

        now_str = self._now()
        doc_ref.update({
            "face_template": None,
            "face_model_version": None,
            "enrollment_consent": False,
            "updated_at": now_str
        })
        self.audit_collection.add({
            "actor_uid": actor_uid,
            "action": "FACE_TEMPLATE_DELETED",
            "target_type": "student",
            "target_id": sid,
            "timestamp": now_str
        })
        return True

    def get_all_enrolled_templates(self) -> list[dict]:
        docs = self.collection.where("status", "==", "active").where("enrollment_consent", "==", True).stream()
        templates = []
        for doc in docs:
            d = doc.to_dict()
            if d.get("face_template"):
                templates.append({
                    "student_id": d["student_id"],
                    "full_name": d["full_name"],
                    "department": d["department"],
                    "face_template": d["face_template"]
                })
        return templates
