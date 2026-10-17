"""
Validation and Security Utility Tests.
Tests student data validation, ID formatting, and CSV formula injection sanitization.
"""

from app.utils.validators import (
    validate_student_id,
    validate_student_data,
    validate_date_str,
    sanitize_csv_cell
)

def test_validate_student_id():
    # Valid IDs
    ok, val = validate_student_id("cs101")
    assert ok is True
    assert val == "CS101"

    ok, val = validate_student_id("STU_2026-A")
    assert ok is True

    # Invalid IDs
    ok, _ = validate_student_id("")
    assert ok is False

    ok, _ = validate_student_id("a")  # too short
    assert ok is False

    ok, _ = validate_student_id("invalid!id#")
    assert ok is False

def test_validate_student_data_create():
    valid_payload = {
        "student_id": "CS202601",
        "full_name": "Aarav Sharma",
        "department": "Computer Science",
        "year_of_study": 3,
        "email": "aarav@college.edu",
        "status": "active"
    }
    is_valid, sanitized, errors = validate_student_data(valid_payload, is_update=False)
    assert is_valid is True
    assert errors == []
    assert sanitized["student_id"] == "CS202601"
    assert sanitized["year_of_study"] == 3

    # Missing required name
    bad_payload = dict(valid_payload)
    bad_payload["full_name"] = " "
    is_valid, _, errors = validate_student_data(bad_payload, is_update=False)
    assert is_valid is False
    assert any("Full name is required" in err for err in errors)

    # Invalid year
    bad_payload = dict(valid_payload)
    bad_payload["year_of_study"] = 10
    is_valid, _, errors = validate_student_data(bad_payload, is_update=False)
    assert is_valid is False
    assert any("Year of study must be between 1 and 8" in err for err in errors)

    # Invalid email
    bad_payload = dict(valid_payload)
    bad_payload["email"] = "not-an-email"
    is_valid, _, errors = validate_student_data(bad_payload, is_update=False)
    assert is_valid is False
    assert any("Invalid email address format" in err for err in errors)

def test_validate_student_data_update():
    update_payload = {
        "full_name": "Updated Name",
        "year_of_study": 4
    }
    is_valid, sanitized, errors = validate_student_data(update_payload, is_update=True)
    assert is_valid is True
    assert sanitized["full_name"] == "Updated Name"
    assert sanitized["year_of_study"] == 4

    # Disallow updating student_id
    update_with_id = {"student_id": "NEWID"}
    is_valid, _, errors = validate_student_data(update_with_id, is_update=True)
    assert is_valid is False
    assert any("cannot be modified" in err for err in errors)

def test_validate_date_str():
    ok, val = validate_date_str("2026-10-17")
    assert ok is True
    assert val == "2026-10-17"

    ok, _ = validate_date_str("2026/10/17")
    assert ok is False

    ok, _ = validate_date_str("invalid-date")
    assert ok is False

    ok, _ = validate_date_str("2026-02-30")  # Invalid calendar day
    assert ok is False

def test_sanitize_csv_cell_formula_injection():
    """Verifies prevention of CSV Formula Injection (CWE-1236)."""
    # Malicious spreadsheet formula triggers
    assert sanitize_csv_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-12+15") == "'-12+15"
    assert sanitize_csv_cell("@HYPERLINK('http://malicious.site')") == "'@HYPERLINK('http://malicious.site')"
    assert sanitize_csv_cell("\tTabPrefixed") == "'\tTabPrefixed"

    # Benign text
    assert sanitize_csv_cell("Aarav Sharma") == "Aarav Sharma"
    assert sanitize_csv_cell("CS202601") == "CS202601"
    assert sanitize_csv_cell("Computer Science") == "Computer Science"
    assert sanitize_csv_cell("") == ""
    assert sanitize_csv_cell(None) == ""
