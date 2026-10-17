"""
Attendance Management, Idempotency, Concurrency, and API Security Tests.
"""

from concurrent.futures import ThreadPoolExecutor
from app import extensions

def test_auth_protection_endpoints(client):
    # Unauthenticated request to /api/students -> 401
    res = client.get("/api/students")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "UNAUTHORIZED"

    # Malformed token format -> 401
    res = client.get("/api/students", headers={"Authorization": "Token 12345"})
    assert res.status_code == 401

    # Invalid token -> 401
    res = client.get("/api/students", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401

def test_admin_role_enforcement(client, user_headers):
    # Student role accessing admin endpoint -> 403
    res = client.get("/api/students", headers=user_headers)
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "FORBIDDEN"

def test_student_lifecycle_and_duplicate_prevention(client, admin_headers, sample_student_payload):
    # 1. Create student
    res = client.post("/api/students", json=sample_student_payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["student_id"] == "TEST2026"
    assert data["full_name"] == "Test Student"

    # 2. Prevent duplicate student_id -> 409
    res_dup = client.post("/api/students", json=sample_student_payload, headers=admin_headers)
    assert res_dup.status_code == 409
    assert res_dup.get_json()["error"]["code"] == "DUPLICATE_STUDENT_ID"

    # 3. Get student profile
    res_get = client.get("/api/students/TEST2026", headers=admin_headers)
    assert res_get.status_code == 200
    assert res_get.get_json()["data"]["student_id"] == "TEST2026"

    # 4. Update student
    res_up = client.put(
        "/api/students/TEST2026",
        json={"full_name": "Updated Name", "year_of_study": 4},
        headers=admin_headers
    )
    assert res_up.status_code == 200
    assert res_up.get_json()["data"]["full_name"] == "Updated Name"
    assert res_up.get_json()["data"]["year_of_study"] == 4

    # 5. Deactivate student
    res_del = client.delete("/api/students/TEST2026", headers=admin_headers)
    assert res_del.status_code == 200
    assert res_del.get_json()["data"]["status"] == "inactive"

def test_attendance_idempotency(client, admin_headers, sample_student_payload):
    # Register student
    client.post("/api/students", json=sample_student_payload, headers=admin_headers)

    # First manual attendance marking
    mark_payload = {
        "student_id": "TEST2026",
        "date": "2026-10-17",
        "session_id": "default",
        "status": "present",
        "notes": "First check-in"
    }
    res1 = client.post("/api/attendance/mark-manual", json=mark_payload, headers=admin_headers)
    assert res1.status_code == 200
    json1 = res1.get_json()["data"]
    assert json1["attendance_status"] == "marked"

    # Second manual attendance marking on the same date/session -> Idempotent response
    res2 = client.post("/api/attendance/mark-manual", json=mark_payload, headers=admin_headers)
    assert res2.status_code == 200
    json2 = res2.get_json()["data"]
    assert json2["attendance_status"] == "already_marked"

    # Verify only 1 record exists in repository
    records = extensions.attendance_repository.get_attendance(student_id="TEST2026", date="2026-10-17")
    assert len(records) == 1

def test_concurrent_attendance_requests():
    """
    Simulates high-concurrency race condition:
    Multiple threads attempting to mark attendance for the same student simultaneously.
    Verifies that exactly ONE write succeeds as 'marked' and all others return 'already_marked'.
    """
    sid = "CONCURRENT_STU"
    att_date = "2026-10-17"
    sess = "default"

    # Seed student
    extensions.student_repository.create({
        "student_id": sid,
        "full_name": "Concurrent Test",
        "department": "Computer Science",
        "year_of_study": 2,
        "email": "concurrent@college.edu",
        "status": "active"
    }, actor_uid="test")

    def perform_mark(thread_id):
        success, status, rec = extensions.attendance_repository.mark_attendance(
            student_id=sid,
            attendance_date=att_date,
            session_id=sess,
            method="face_recognition",
            actor_uid=f"thread_{thread_id}",
            status="present"
        )
        return status

    num_threads = 10
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(perform_mark, range(num_threads)))

    marked_count = results.count("marked")
    already_marked_count = results.count("already_marked")

    assert marked_count == 1, f"Expected exactly 1 'marked', got {marked_count}"
    assert already_marked_count == num_threads - 1

    records = extensions.attendance_repository.get_attendance(student_id=sid, date=att_date)
    assert len(records) == 1

def test_dashboard_metrics_and_csv_export(client, admin_headers, sample_student_payload):
    # Register student
    client.post("/api/students", json=sample_student_payload, headers=admin_headers)

    # Mark attendance
    client.post("/api/attendance/mark-manual", json={
        "student_id": "TEST2026",
        "date": "2026-10-17",
        "status": "present",
        "notes": "Verified by Proctor"
    }, headers=admin_headers)

    # Dashboard endpoint
    res_dash = client.get("/api/dashboard", headers=admin_headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.get_json()["data"]
    assert dash_data["summary"]["present_today"] >= 1
    assert "trend" in dash_data
    assert len(dash_data["trend"]) == 7

    # CSV Export endpoint
    res_csv = client.get("/api/attendance/export?date=2026-10-17", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers.get("Content-Type", "")
    csv_text = res_csv.get_data(as_text=True)
    assert "Attendance ID,Student ID,Student Name" in csv_text
    assert "TEST2026" in csv_text
