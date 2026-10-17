# Testing Guide & Quality Assurance

This document outlines the test strategy, automated test suites, concurrency testing, and manual verification procedures for the **Student Attendance Management System**.

---

## 1. Automated Test Suites (Pytest)

The test suite in `backend/tests/` includes 20 automated test cases categorized into four core suites:

```
backend/tests/
├── conftest.py            # Test app factory, clean database fixtures, mock tokens
├── test_health.py         # Liveness probe, model status, and CORS headers
├── test_validation.py     # Student schemas, date validation, CSV injection defense
├── test_recognition.py    # Cosine similarity math, SFace matching, ambiguity checks
└── test_attendance.py     # Idempotency, high-concurrency race conditions, reports
```

### Key Areas Tested:
1. **Health & Diagnostics** (`test_health.py`):
   - Verifies HTTP 200 response from `/api/health`.
   - Confirms detection model (YuNet) and recognizer (SFace) status reporting.
   - Verifies CORS headers for preflight requests.
2. **Data Integrity & Security** (`test_validation.py`):
   - Validates student ID regex (`^[A-Za-z0-9_-]{2,30}$`).
   - Validates full name length, department validity, and year bounds (1-8).
   - Enforces CSV Formula Injection sanitization (CWE-1236): verifies that values starting with `=`, `+`, `-`, `@`, `\t` are prefixed with `'`.
3. **Computer Vision & Ambiguity** (`test_recognition.py`):
   - Validates Cosine Similarity math on unit, orthogonal, and opposite vectors.
   - Validates multi-sample template aggregation ($L_2$ norm $\approx 1.0$).
   - Validates threshold rejection of unknown subjects.
   - Validates **Ambiguity Rejection**: when top-1 and top-2 candidate difference is narrower than `match_margin` ($0.080$), automatic attendance is rejected.
   - Validates image blur detection via Laplacian variance.
4. **Attendance Idempotency & High Concurrency** (`test_attendance.py`):
   - Verifies that re-submitting attendance for the same student on the same date returns `already_marked` without creating duplicates.
   - **Concurrency Stress Test**: Uses `concurrent.futures.ThreadPoolExecutor` to dispatch 10 simultaneous requests for the same student. Asserts that exactly 1 write succeeds as `marked`, 9 return `already_marked`, and exactly 1 record is persisted.
   - Verifies server-side Firebase ID token verification and admin role protection.

---

## 2. Running Automated Tests

Run all unit and integration tests with verbose output:

```bash
python -m pytest backend/tests -v
```

Expected output:
```
backend/tests/test_attendance.py::test_auth_protection_endpoints PASSED
backend/tests/test_attendance.py::test_admin_role_enforcement PASSED
backend/tests/test_attendance.py::test_student_lifecycle_and_duplicate_prevention PASSED
backend/tests/test_attendance.py::test_attendance_idempotency PASSED
backend/tests/test_attendance.py::test_concurrent_attendance_requests PASSED
backend/tests/test_attendance.py::test_dashboard_metrics_and_csv_export PASSED
backend/tests/test_health.py::test_health_check_returns_200 PASSED
backend/tests/test_health.py::test_health_check_cors_headers PASSED
backend/tests/test_recognition.py::test_cosine_similarity_math PASSED
backend/tests/test_recognition.py::test_template_aggregation PASSED
backend/tests/test_recognition.py::test_identify_known_subject PASSED
backend/tests/test_recognition.py::test_identify_unknown_subject PASSED
backend/tests/test_recognition.py::test_identify_ambiguity_rejection PASSED
backend/tests/test_recognition.py::test_identify_no_enrolled_students PASSED
backend/tests/test_recognition.py::test_face_detector_blur_computation PASSED
backend/tests/test_validation.py::test_validate_student_id PASSED
backend/tests/test_validation.py::test_validate_student_data_create PASSED
backend/tests/test_validation.py::test_validate_student_data_update PASSED
backend/tests/test_validation.py::test_validate_date_str PASSED
backend/tests/test_validation.py::test_sanitize_csv_cell_formula_injection PASSED
============================= 20 passed in 0.43s ==============================
```

---

## 3. Manual Webcam & End-to-End Testing

1. **Start the backend**:
   ```bash
   python backend/run.py
   ```
2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in a modern browser (Google Chrome, Microsoft Edge, or Firefox).
4. Click **"Instant One-Click Admin Demo Login"**.
5. Navigate to **Face Enrollment**:
   - Select a student (e.g. `CS202601`).
   - Check the **Biometric Consent** checkbox.
   - Click **Start Camera** and grant browser webcam permissions.
   - Click **Capture Sample** 3 to 5 times while looking straight, slightly angled left, and slightly angled right.
   - Click **Complete Face Enrollment**.
6. Navigate to **Live Attendance**:
   - Click **Start Camera**.
   - Check **Auto-Scan Mode (2s)** or click **Scan Now**.
   - Verify that your face matches the enrolled student, marking them **Present** with green confirmation and check-in time recorded in the session log.
   - Scan again to verify the yellow **Already Marked** idempotent status.
7. Navigate to **Attendance History**:
   - Inspect today's records.
   - Click **Export CSV** and open the file in Excel or Sheets to verify escaped formulas and clean columns.
