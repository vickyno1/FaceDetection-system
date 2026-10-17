"""
Face Detection Service using OpenCV YuNet.
Handles frame preprocessing, face localization, facial landmark extraction,
and face quality verification (size, confidence, sharpness/blur).
"""

import os
from pathlib import Path
import cv2
import numpy as np

class FaceDetectionError(Exception):
    pass

class FaceDetector:
    def __init__(self, model_path: str = None, conf_threshold: float = 0.80, nms_threshold: float = 0.30):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.detector = None
        self._current_input_size = (320, 320)
        
        if self.model_path and Path(self.model_path).exists():
            self._init_detector()

    def _init_detector(self):
        try:
            self.detector = cv2.FaceDetectorYN.create(
                model=str(self.model_path),
                config="",
                input_size=self._current_input_size,
                score_threshold=self.conf_threshold,
                nms_threshold=self.nms_threshold,
                top_k=5000,
                backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                target_id=cv2.dnn.DNN_TARGET_CPU
            )
        except Exception as e:
            raise FaceDetectionError(f"Failed to initialize YuNet detector: {str(e)}")

    def compute_blur_score(self, face_bgr: np.ndarray) -> float:
        """Computes blur metric using Laplacian variance. Higher = sharper."""
        if face_bgr is None or face_bgr.size == 0:
            return 0.0
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def detect_faces(self, image_bgr: np.ndarray) -> list[dict]:
        """
        Detects all faces in the provided BGR image.
        Returns a list of structured face dictionaries.
        """
        if self.detector is None:
            if self.model_path and Path(self.model_path).exists():
                self._init_detector()
            else:
                raise FaceDetectionError("YuNet model file is not available or not initialized.")

        if image_bgr is None or image_bgr.size == 0:
            return []

        h, w = image_bgr.shape[:2]
        if (w, h) != self._current_input_size:
            self._current_input_size = (w, h)
            self.detector.setInputSize((w, h))

        retval, raw_faces = self.detector.detect(image_bgr)
        if raw_faces is None or len(raw_faces) == 0:
            return []

        results = []
        for face_arr in raw_faces:
            # YuNet array structure (15 elements):
            # [0:4] = x, y, w, h
            # [4:14] = 5 landmarks (x, y for right_eye, left_eye, nose_tip, right_mouth, left_mouth)
            # [14] = confidence score
            box = face_arr[0:4].astype(int)
            x, y, fw, fh = box[0], box[1], box[2], box[3]
            conf = float(face_arr[14])

            # Clamp face crop box to image bounds for quality inspection
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w, x + fw)
            y2 = min(h, y + fh)

            face_crop = image_bgr[y1:y2, x1:x2] if (x2 > x1 and y2 > y1) else None
            blur_score = self.compute_blur_score(face_crop) if face_crop is not None else 0.0

            landmarks = {
                "right_eye": (float(face_arr[4]), float(face_arr[5])),
                "left_eye": (float(face_arr[6]), float(face_arr[7])),
                "nose_tip": (float(face_arr[8]), float(face_arr[9])),
                "right_mouth": (float(face_arr[10]), float(face_arr[11])),
                "left_mouth": (float(face_arr[12]), float(face_arr[13]))
            }

            results.append({
                "bbox": {"x": int(x), "y": int(y), "w": int(fw), "h": int(fh)},
                "confidence": round(conf, 4),
                "blur_score": round(blur_score, 2),
                "landmarks": landmarks,
                "_raw_face": face_arr  # Needed for SFace alignCrop
            })

        return results

    def validate_for_enrollment(
        self,
        image_bgr: np.ndarray,
        min_size: int = 60,
        min_blur_score: float = 30.0
    ) -> dict:
        """
        Validates an image specifically for face enrollment.
        Enforces:
        - Exactly one face present
        - Bounding box >= min_size
        - Sharpness >= min_blur_score
        """
        faces = self.detect_faces(image_bgr)

        if len(faces) == 0:
            return {
                "valid": False,
                "error_code": "NO_FACE_DETECTED",
                "message": "No face detected in the frame. Please look directly at the camera."
            }

        if len(faces) > 1:
            return {
                "valid": False,
                "error_code": "MULTIPLE_FACES_DETECTED",
                "message": f"Multiple faces ({len(faces)}) detected. Enrollment requires exactly one subject in frame."
            }

        face = faces[0]
        bw, bh = face["bbox"]["w"], face["bbox"]["h"]
        if bw < min_size or bh < min_size:
            return {
                "valid": False,
                "error_code": "FACE_TOO_SMALL",
                "message": f"Face is too small ({bw}x{bh}px). Please move closer to the camera (minimum {min_size}x{min_size}px)."
            }

        if face["blur_score"] < min_blur_score:
            return {
                "valid": False,
                "error_code": "FACE_BLURRED",
                "message": f"Image is too blurry (sharpness score {face['blur_score']:.1f}). Please stay still under good lighting."
            }

        return {
            "valid": True,
            "face": face
        }
