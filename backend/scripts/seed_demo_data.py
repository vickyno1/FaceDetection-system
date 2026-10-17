"""
Demo Data Seeding Script.
Populates students, sample biometric embeddings, and attendance records
for academic demonstrations and portfolio evaluation.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np

# Add parent directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import Config
import app.extensions as extensions

DEMO_STUDENTS = [
    {
        "student_id": "CS202601",
        "full_name": "Aarav Sharma",
        "department": "Computer Science",
        "year_of_study": 3,
        "email": "aarav.sharma@college.edu",
        "status": "active"
    },
    {
        "student_id": "CS202602",
        "full_name": "Diya Patel",
        "department": "Computer Science",
        "year_of_study": 3,
        "email": "diya.patel@college.edu",
        "status": "active"
    },
    {
        "student_id": "IT202603",
        "full_name": "Rohan Verma",
        "department": "Information Technology",
        "year_of_study": 2,
        "email": "rohan.verma@college.edu",
        "status": "active"
    },
    {
        "student_id": "AI202604",
        "full_name": "Ananya Iyer",
        "department": "Artificial Intelligence",
        "year_of_study": 4,
        "email": "ananya.iyer@college.edu",
        "status": "active"
    },
    {
        "student_id": "DS202605",
        "full_name": "Vikram Malhotra",
        "department": "Data Science",
        "year_of_study": 1,
        "email": "vikram.malhotra@college.edu",
        "status": "active"
    },
    {
        "student_id": "EC202606",
        "full_name": "Pooja Hegde",
        "department": "Electronics & Communication",
        "year_of_study": 2,
        "email": "pooja.hegde@college.edu",
        "status": "active"
    },
    {
        "student_id": "ME202607",
        "full_name": "Siddharth Rao",
        "department": "Mechanical Engineering",
        "year_of_study": 3,
        "email": "siddharth.rao@college.edu",
        "status": "inactive"
    }
]

def generate_synthetic_embedding(seed: int) -> list[float]:
    """Generates a deterministic, normalized 128-D vector for demonstration."""
    rng = np.random.RandomState(seed)
    vec = rng.randn(128).astype(np.float32)
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist()

def seed_data():
    app = create_app()
    with app.app_context():
        print("[*] Seeding Demo Students and Biometrics...")
        actor_uid = "system_seed_script"

        created_count = 0
        for idx, s_data in enumerate(DEMO_STUDENTS):
            sid = s_data["student_id"]
            existing = extensions.student_repository.get_by_id(sid)
            if not existing:
                extensions.student_repository.create(s_data, actor_uid=actor_uid)
                created_count += 1
                print(f"  + Created student: {sid} - {s_data['full_name']}")
            else:
                print(f"  = Student already exists: {sid}")

            # Enroll synthetic face template for the first 5 active students
            if idx < 5:
                emb = generate_synthetic_embedding(1000 + idx)
                extensions.student_repository.save_face_template(
                    student_id=sid,
                    template=emb,
                    model_version="sface_2021dec",
                    consent=True,
                    actor_uid=actor_uid
                )
                print(f"    [OK] Biometric template enrolled for {sid}")

        print(f"\n[*] Seeding Historical and Today's Attendance Records...")
        tz_name = Config.ATTENDANCE_TIMEZONE
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc

        now = datetime.now(tz)
        today_date = now.strftime("%Y-%m-%d")

        # Seed attendance for past 6 days + today
        active_ids = [s["student_id"] for s in DEMO_STUDENTS if s["status"] == "active"]

        attendance_count = 0
        for day_offset in range(6, -1, -1):
            date_str = (now - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            # Vary attendance per day to make the trend chart realistic
            for i, sid in enumerate(active_ids):
                # If offset is 0 (today), mark first 4 students
                if day_offset == 0 and i >= 4:
                    continue
                # For past days, create varied attendance
                if (day_offset + i) % 5 == 0:
                    continue  # Absent on this day

                method = "face_recognition" if (i % 2 == 0) else "manual"
                notes = "Automated kiosk face match" if method == "face_recognition" else "Manual roll-call entry"

                success, status, record = extensions.attendance_repository.mark_attendance(
                    student_id=sid,
                    attendance_date=date_str,
                    session_id="default",
                    method=method,
                    actor_uid=actor_uid,
                    status="present",
                    tz_name=tz_name,
                    notes=notes
                )
                if status == "marked":
                    attendance_count += 1

        print(f"  + Seeded {attendance_count} attendance records across 7 days.")
        print("\n[SUCCESS] Seeding complete! Database is populated with realistic demonstration data.")

if __name__ == "__main__":
    seed_data()
