"""
Face Recognition, Embeddings, and Identification Tests.
Tests cosine similarity mathematics, candidate ambiguity checks,
template aggregation, and unknown face rejection.
"""

import numpy as np
from app.services.face_recognizer import FaceRecognizer
from app.services.face_detector import FaceDetector

def test_cosine_similarity_math():
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    v4 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)

    # Identical vectors -> 1.0
    sim_ident = FaceRecognizer.cosine_similarity(v1, v2)
    assert abs(sim_ident - 1.0) < 1e-5

    # Orthogonal vectors -> 0.0
    sim_ortho = FaceRecognizer.cosine_similarity(v1, v3)
    assert abs(sim_ortho - 0.0) < 1e-5

    # Opposite vectors -> -1.0
    sim_opp = FaceRecognizer.cosine_similarity(v1, v4)
    assert abs(sim_opp - (-1.0)) < 1e-5

    # Magnitude invariance
    v_scaled = v1 * 5.0
    assert abs(FaceRecognizer.cosine_similarity(v1, v_scaled) - 1.0) < 1e-5

def test_template_aggregation():
    # 3 sample vectors
    rng = np.random.RandomState(42)
    v1 = rng.randn(128).astype(np.float32)
    v2 = rng.randn(128).astype(np.float32)
    v3 = rng.randn(128).astype(np.float32)

    aggregated = FaceRecognizer.aggregate_templates([v1, v2, v3])
    assert len(aggregated) == 128
    # Norm must be 1.0
    norm = np.linalg.norm(np.array(aggregated, dtype=np.float32))
    assert abs(norm - 1.0) < 1e-4

def test_identify_known_subject(synthetic_vector):
    recognizer = FaceRecognizer(threshold=0.380, match_margin=0.080)

    target_emb = synthetic_vector(100)
    other_emb1 = synthetic_vector(200)
    other_emb2 = synthetic_vector(300)

    enrolled = [
        {"student_id": "STU1", "full_name": "Target Student", "department": "CS", "face_template": target_emb},
        {"student_id": "STU2", "full_name": "Student Two", "department": "IT", "face_template": other_emb1},
        {"student_id": "STU3", "full_name": "Student Three", "department": "DS", "face_template": other_emb2},
    ]

    # Query with identical embedding
    res = recognizer.identify(np.array(target_emb), enrolled)
    assert res["status"] == "MATCH"
    assert res["matched_student"]["student_id"] == "STU1"
    assert res["similarity_score"] >= 0.99

def test_identify_unknown_subject(synthetic_vector):
    recognizer = FaceRecognizer(threshold=0.400, match_margin=0.080)

    emb1 = synthetic_vector(1)
    emb2 = synthetic_vector(2)
    unknown_query = synthetic_vector(999)  # completely different seed

    enrolled = [
        {"student_id": "STU1", "full_name": "Student One", "face_template": emb1},
        {"student_id": "STU2", "full_name": "Student Two", "face_template": emb2},
    ]

    res = recognizer.identify(np.array(unknown_query), enrolled)
    # Random orthogonal vectors in 128-D have similarity close to 0 (< 0.25)
    assert res["status"] == "UNKNOWN_FACE"
    assert res["matched_student"] is None

def test_identify_ambiguity_rejection():
    """Verifies that when top-1 and top-2 candidates are too close, match is rejected."""
    recognizer = FaceRecognizer(threshold=0.350, match_margin=0.080)

    base = np.random.RandomState(42).randn(128).astype(np.float32)
    base = base / np.linalg.norm(base)

    # Slight perturbation for student 1 (sim ~ 0.98)
    cand1 = base + np.random.RandomState(1).randn(128) * 0.05
    cand1 = (cand1 / np.linalg.norm(cand1)).tolist()

    # Slight perturbation for student 2 (sim ~ 0.96)
    cand2 = base + np.random.RandomState(2).randn(128) * 0.06
    cand2 = (cand2 / np.linalg.norm(cand2)).tolist()

    enrolled = [
        {"student_id": "STU1", "full_name": "Twin One", "face_template": cand1},
        {"student_id": "STU2", "full_name": "Twin Two", "face_template": cand2},
    ]

    # Query with base vector
    res = recognizer.identify(base, enrolled)
    # Both cand1 and cand2 are very close to base, so difference < match_margin (0.080)
    assert res["status"] == "AMBIGUOUS_MATCH"
    assert res["matched_student"] is None
    assert res["confidence_margin"] < 0.080

def test_identify_no_enrolled_students(synthetic_vector):
    recognizer = FaceRecognizer(threshold=0.380)
    query = synthetic_vector(42)
    res = recognizer.identify(np.array(query), [])
    assert res["status"] == "NO_ENROLLED_STUDENTS"
    assert res["matched_student"] is None

def test_face_detector_blur_computation():
    detector = FaceDetector(model_path=None)
    # Uniform black image -> blur score 0.0
    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    score = detector.compute_blur_score(blank)
    assert score == 0.0

    # High frequency textured image -> higher variance
    textured = (np.random.RandomState(42).rand(100, 100, 3) * 255).astype(np.uint8)
    tex_score = detector.compute_blur_score(textured)
    assert tex_score > 50.0
