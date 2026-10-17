"""
Input Validation and Sanitization Utilities.
Protects against invalid formats, malicious inputs, and CSV formula injection.
"""

import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
STUDENT_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{2,30}$")

VALID_DEPARTMENTS = {
    "Computer Science",
    "Information Technology",
    "Electronics & Communication",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electrical Engineering",
    "Data Science",
    "Artificial Intelligence",
    "Business Administration"
}

def validate_student_id(student_id: str) -> tuple[bool, str]:
    if not student_id or not isinstance(student_id, str):
        return False, "Student ID is required."
    clean_id = student_id.strip()
    if not STUDENT_ID_REGEX.match(clean_id):
        return False, "Student ID must be 2-30 alphanumeric characters, hyphens or underscores."
    return True, clean_id.upper()

def validate_student_data(data: dict, is_update: bool = False) -> tuple[bool, dict, list[str]]:
    """
    Validates student payload fields.
    Returns: (is_valid, sanitized_dict, error_list)
    """
    errors = []
    sanitized = {}

    if not isinstance(data, dict):
        return False, {}, ["Request body must be a JSON object."]

    # Student ID
    if not is_update:
        valid_id, result = validate_student_id(data.get("student_id", ""))
        if not valid_id:
            errors.append(result)
        else:
            sanitized["student_id"] = result
    elif "student_id" in data:
        # Student ID cannot be modified on update
        errors.append("Student ID cannot be modified after registration.")

    # Full Name
    if "full_name" in data or not is_update:
        full_name = data.get("full_name", "")
        if not full_name or not isinstance(full_name, str) or len(full_name.strip()) < 2:
            errors.append("Full name is required and must have at least 2 characters.")
        elif len(full_name.strip()) > 100:
            errors.append("Full name cannot exceed 100 characters.")
        else:
            sanitized["full_name"] = full_name.strip()

    # Department
    if "department" in data or not is_update:
        dept = data.get("department", "")
        if not dept or not isinstance(dept, str) or len(dept.strip()) < 2:
            errors.append("Department is required.")
        else:
            sanitized["department"] = dept.strip()

    # Year of Study
    if "year_of_study" in data or not is_update:
        year = data.get("year_of_study")
        try:
            year_int = int(year)
            if not (1 <= year_int <= 8):
                errors.append("Year of study must be between 1 and 8.")
            else:
                sanitized["year_of_study"] = year_int
        except (ValueError, TypeError):
            errors.append("Year of study must be a valid integer.")

    # Email (optional)
    if "email" in data:
        email = data.get("email")
        if email:
            email_clean = str(email).strip()
            if not EMAIL_REGEX.match(email_clean):
                errors.append("Invalid email address format.")
            else:
                sanitized["email"] = email_clean.lower()
        else:
            sanitized["email"] = ""
    elif not is_update:
        sanitized["email"] = ""

    # Status
    if "status" in data:
        status = str(data.get("status", "")).strip().lower()
        if status not in ("active", "inactive"):
            errors.append("Status must be either 'active' or 'inactive'.")
        else:
            sanitized["status"] = status
    elif not is_update:
        sanitized["status"] = "active"

    return len(errors) == 0, sanitized, errors

def validate_date_str(date_str: str) -> tuple[bool, str]:
    """Validates date format YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return False, "Date string is required."
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True, dt.strftime("%Y-%m-%d")
    except ValueError:
        return False, "Date must be in format YYYY-MM-DD."

def sanitize_csv_cell(value) -> str:
    """
    Prevents CSV Formula Injection (CWE-1236).
    If a cell value starts with '=', '+', '-', '@', tab, or carriage return,
    prefix it with a single quote so spreadsheets treat it strictly as plain text.
    """
    if value is None:
        return ""
    val_str = str(value)
    if not val_str:
        return ""
    dangerous_prefixes = ("=", "+", "-", "@", "\t", "\r")
    if val_str.startswith(dangerous_prefixes):
        return "'" + val_str
    return val_str
