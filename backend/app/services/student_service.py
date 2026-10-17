"""
Student Service Layer.
Business logic for managing student profiles, consent verification,
and face enrollment processing.
"""

import base64
import cv2
import numpy as np
from ..repositories.student_repository import BaseStudentRepository
from .face_detector import FaceDetector
from .face_recognizer import FaceRecognizer

class StudentService:
    def __init__(self, student_repo: BaseStudentRepository, detector: FaceDetector, recognizer: FaceRecognizer):
        self.student_repo = student_repo
        self.detector = detector
        self.recognizer = recognizer

    def get_student(self, student_id: str) -> dict | None:
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return None
        res = dict(student)
        res["has_face_enrolled"] = bool(student.get("face_template"))
        res.pop("face_template", None)
        return res

    def list_students(self, department: str = None, status: str = None, search: str = None) -> list[dict]:
        return self.student_repo.list_students(department=department, status=status, search=search)

    def create_student(self, data: dict, actor_uid: str) -> dict:
        return self.student_repo.create(data, actor_uid)

    def update_student(self, student_id: str, data: dict, actor_uid: str) -> dict | None:
        return self.student_repo.update(student_id, data, actor_uid)

    def deactivate_student(self, student_id: str, actor_uid: str) -> bool:
        return self.student_repo.deactivate(student_id, actor_uid)

    def decode_base64_image(self, b64_str: str) -> np.ndarray | None:
        """Decodes a base64 encoded image string (supports data URL prefix)."""
        try:
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]
            img_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img_bgr
        except Exception:
            return None

    def enroll_face(self, student_id: str, image_b64_list: list[str], consent: bool, actor_uid: str) -> dict:
        """
        Enrolls a student's facial template from a set of captured frames.
        Enforces:
        - Explicit documented consent
        - Verification that student exists and is active
        - Quality validation on each captured frame
        - Aggregation of 128-D SFace feature vectors into a normalized template
        """
        if not consent:
            return {
                "success": False,
                "error_code": "CONSENT_REQUIRED",
                "message": "Explicit consent is required for biometric face enrollment."
            }

        student = self.student_repo.get_by_id(student_id)
        if not student:
            return {
                "success": False,
                "error_code": "STUDENT_NOT_FOUND",
                "message": f"Student with ID '{student_id}' does not exist."
            }

        if student.get("status") != "active":
            return {
                "success": False,
                "error_code": "STUDENT_INACTIVE",
                "message": f"Student '{student_id}' is inactive. Activate student before enrolling face."
            }

        if not image_b64_list or len(image_b64_list) < 1:
            return {
                "success": False,
                "error_code": "NO_IMAGES_PROVIDED",
                "message": "At least one face image capture is required for enrollment."
            }

        valid_vectors = []
        frame_diagnostics = []

        for idx, b64_data in enumerate(image_b64_list):
            img_bgr = self.decode_base64_image(b64_data)
            if img_bgr is None:
                frame_diagnostics.append({"frame": idx + 1, "status": "FAILED", "reason": "Corrupted or invalid image data."})
                continue

            val_res = self.detector.validate_for_enrollment(img_bgr)
            if not val_res["valid"]:
                frame_diagnostics.append({"frame": idx + 1, "status": "REJECTED", "reason": val_res["message"]})
                continue

            face = val_res["face"]
            try:
                feature_vec = self.recognizer.extract_feature(img_bgr, face["_raw_face"])
                valid_vectors.append(feature_vec)
                frame_diagnostics.append({
                    "frame": idx + 1,
                    "status": "ACCEPTED",
                    "confidence": face["confidence"],
                    "blur_score": face["blur_score"],
                    "box": face["bbox"]
                })
            except Exception as e:
                frame_diagnostics.append({"frame": idx + 1, "status": "FAILED", "reason": f"Feature extraction error: {str(e)}"})

        if len(valid_vectors) == 0:
            return {
                "success": False,
                "error_code": "ALL_FRAMES_REJECTED",
                "message": "All captured frames were rejected due to poor quality, missing faces, or blur.",
                "diagnostics": frame_diagnostics
            }

        # Aggregate valid vectors into normalized template
        aggregated_template = self.recognizer.aggregate_templates(valid_vectors)

        saved = self.student_repo.save_face_template(
            student_id=student_id,
            template=aggregated_template,
            model_version="sface_2021dec",
            consent=True,
            actor_uid=actor_uid
        )

        return {
            "success": saved,
            "student_id": student_id,
            "frames_accepted": len(valid_vectors),
            "frames_submitted": len(image_b64_list),
            "model_version": "sface_2021dec",
            "diagnostics": frame_diagnostics
        }

    def delete_face_template(self, student_id: str, actor_uid: str) -> bool:
        return self.student_repo.delete_face_template(student_id, actor_uid)
