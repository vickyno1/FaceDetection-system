"""
Pytest Fixtures for Automated Testing.
Configures test Flask client, in-memory repositories, and sample test data.
"""

import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import numpy as np
from app import create_app
from app.config import TestConfig
import app.extensions as extensions

@pytest.fixture(scope="session")
def app():
    test_app = create_app(TestConfig)
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db(app):
    """Clears in-memory repositories before each test."""
    with app.app_context():
        if extensions.student_repository and hasattr(extensions.student_repository, "students"):
            extensions.student_repository.students.clear()
            extensions.student_repository.audit_logs.clear()
        if extensions.attendance_repository and hasattr(extensions.attendance_repository, "records"):
            extensions.attendance_repository.records.clear()
            extensions.attendance_repository.audit_logs.clear()

@pytest.fixture
def admin_headers():
    return {
        "Authorization": "Bearer mock-admin-token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def user_headers():
    return {
        "Authorization": "Bearer user-token-regular",
        "Content-Type": "application/json"
    }

@pytest.fixture
def sample_student_payload():
    return {
        "student_id": "TEST2026",
        "full_name": "Test Student",
        "department": "Computer Science",
        "year_of_study": 3,
        "email": "test.student@college.edu",
        "status": "active"
    }

@pytest.fixture
def synthetic_vector():
    def _create(seed=42):
        rng = np.random.RandomState(seed)
        v = rng.randn(128).astype(np.float32)
        return (v / np.linalg.norm(v)).tolist()
    return _create
