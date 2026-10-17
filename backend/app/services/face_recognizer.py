"""
Face Recognition Service using OpenCV SFace.
Performs face alignment, 128-D feature vector extraction, cosine similarity calculation,
and ambiguous candidate match resolution.
"""

from pathlib import Path
import cv2
import numpy as np

class FaceRecognitionError(Exception):
    pass

class FaceRecognizer:
    def __init__(self, model_path: str = None, threshold: float = 0.380, match_margin: float = 0.080):
        self.model_path = model_path
        self.threshold = threshold
        self.match_margin = match_margin
        self.recognizer = None

        if self.model_path and Path(self.model_path).exists():
            self._init_recognizer()

    def _init_recognizer(self):
        try:
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=str(self.model_path),
                config="",
                backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                target_id=cv2.dnn.DNN_TARGET_CPU
            )
        except Exception as e:
            raise FaceRecognitionError(f"Failed to initialize SFace recognizer: {str(e)}")

    def extract_feature(self, image_bgr: np.ndarray, raw_face_arr: np.ndarray) -> np.ndarray:
        """
        Aligns the face using landmark coordinates and extracts a 128-D embedding.
        Returns a normalized 1D numpy array of float32 values.
        """
        if self.recognizer is None:
            if self.model_path and Path(self.model_path).exists():
                self._init_recognizer()
            else:
                raise FaceRecognitionError("SFace model file is not available or not initialized.")

        aligned_face = self.recognizer.alignCrop(image_bgr, raw_face_arr)
        feature = self.recognizer.feature(aligned_face)
        # feature has shape (1, 128)
        feature_vec = feature.flatten().astype(np.float32)
        norm = np.linalg.norm(feature_vec)
        if norm > 0:
            feature_vec = feature_vec / norm
        return feature_vec

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Computes cosine similarity between two 1D vectors."""
        v1 = np.asarray(vec1, dtype=np.float32).flatten()
        v2 = np.asarray(vec2, dtype=np.float32).flatten()
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = np.dot(v1, v2)
        return float(dot / (norm1 * norm2))

    @staticmethod
    def aggregate_templates(feature_vectors: list[np.ndarray]) -> list[float]:
        """
        Aggregates multiple face feature vectors (e.g., from 3-5 enrollment captures)
        into a robust, normalized representative template.
        """
        if not feature_vectors:
            raise ValueError("Cannot aggregate empty list of feature vectors.")

        normed_vectors = []
        for vec in feature_vectors:
            v = np.asarray(vec, dtype=np.float32).flatten()
            norm = np.linalg.norm(v)
            if norm > 0:
                normed_vectors.append(v / norm)

        mean_vector = np.mean(normed_vectors, axis=0)
        mean_norm = np.linalg.norm(mean_vector)
        if mean_norm > 0:
            mean_vector = mean_vector / mean_norm
        return mean_vector.tolist()

    def identify(
        self,
        query_vector: np.ndarray,
        enrolled_students: list[dict],
        threshold: float = None,
        match_margin: float = None
    ) -> dict:
        """
        Compares query feature vector against enrolled student templates.
        Enforces:
        - Configurable threshold (default self.threshold)
        - Ambiguity check: Top-1 vs Top-2 margin (default self.match_margin)
        Returns:
            {
                "status": "MATCH" | "AMBIGUOUS_MATCH" | "UNKNOWN_FACE" | "NO_ENROLLED_STUDENTS",
                "matched_student": dict or None,
                "similarity_score": float,
                "confidence_margin": float or None,
                "candidates": list of top candidates
            }
        """
        sim_threshold = self.threshold if threshold is None else threshold
        margin = self.match_margin if match_margin is None else match_margin

        if not enrolled_students:
            return {
                "status": "NO_ENROLLED_STUDENTS",
                "matched_student": None,
                "similarity_score": 0.0,
                "confidence_margin": None,
                "candidates": []
            }

        candidates = []
        for student in enrolled_students:
            template = student.get("face_template")
            if not template:
                continue
            sim = self.cosine_similarity(query_vector, template)
            candidates.append({
                "student_id": student.get("student_id"),
                "full_name": student.get("full_name"),
                "department": student.get("department"),
                "similarity": round(float(sim), 4)
            })

        if not candidates:
            return {
                "status": "NO_ENROLLED_STUDENTS",
                "matched_student": None,
                "similarity_score": 0.0,
                "confidence_margin": None,
                "candidates": []
            }

        # Sort descending by similarity
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        top1 = candidates[0]
        top1_score = top1["similarity"]

        # Check if top candidate meets similarity threshold
        if top1_score < sim_threshold:
            return {
                "status": "UNKNOWN_FACE",
                "matched_student": None,
                "similarity_score": top1_score,
                "confidence_margin": None,
                "candidates": candidates[:3]
            }

        # Check ambiguity if second candidate exists
        if len(candidates) > 1:
            top2 = candidates[1]
            top2_score = top2["similarity"]
            diff = top1_score - top2_score

            # If the difference between top 1 and top 2 is narrower than the margin,
            # and top 2 is also a plausible candidate, flag as ambiguous!
            if diff < margin and top2_score >= (sim_threshold - 0.10):
                return {
                    "status": "AMBIGUOUS_MATCH",
                    "matched_student": None,
                    "similarity_score": top1_score,
                    "confidence_margin": round(diff, 4),
                    "candidates": candidates[:3],
                    "message": f"Ambiguous match between {top1['student_id']} ({top1_score:.3f}) and {top2['student_id']} ({top2_score:.3f}). Margin {diff:.3f} is less than required {margin:.3f}."
                }

        # Passed both threshold and ambiguity check
        return {
            "status": "MATCH",
            "matched_student": {
                "student_id": top1["student_id"],
                "full_name": top1["full_name"],
                "department": top1["department"]
            },
            "similarity_score": top1_score,
            "confidence_margin": round(top1_score - candidates[1]["similarity"], 4) if len(candidates) > 1 else 1.0,
            "candidates": candidates[:3]
        }
