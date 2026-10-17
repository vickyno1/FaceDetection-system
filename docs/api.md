# REST API Specification

This document details all REST endpoints provided by the **Student Attendance Management System** backend.

**Base URL**: `/api` (or `http://localhost:5000/api`)

---

## 1. Authentication & Security

All protected endpoints require an HTTP `Authorization` header containing a valid Bearer token:

```http
Authorization: Bearer <firebase_id_token_or_mock_admin_token>
```

- In production, tokens are verified via the Firebase Admin SDK (`firebase_admin.auth.verify_id_token`).
- In mock/development mode, `mock-admin-token` grants administrative privileges.
- Standard HTTP Status Codes:
  - `200 OK`: Successful retrieval or idempotent completion.
  - `201 Created`: Resource successfully created.
  - `400 Bad Request`: Malformed payload or validation error.
  - `401 Unauthorized`: Missing, invalid, or expired authentication token.
  - `403 Forbidden`: Insufficient role or privileges.
  - `404 Not Found`: Target resource does not exist.
  - `409 Conflict`: Duplicate unique key (e.g. existing Student ID).
  - `413 Payload Too Large`: Request body exceeds 16MB.
  - `422 Unprocessable Entity`: Semantic/model processing failure (e.g. blurry image).
  - `500 Internal Server Error`: Unhandled server exception.

---

## 2. Endpoints Overview

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Public | Liveness check, loaded model diagnostics, and server timezone. |
| `GET` | `/api/dashboard` | Admin | Dashboard summary statistics, recent check-ins, and 7-day trend. |
| `GET` | `/api/students` | Admin | List students with search and department filtering. |
| `POST` | `/api/students` | Admin | Register a new student profile. |
| `GET` | `/api/students/{id}` | Admin | Retrieve individual student profile. |
| `PUT` | `/api/students/{id}` | Admin | Update student profile fields. |
| `DELETE` | `/api/students/{id}` | Admin | Soft-deactivate student. |
| `POST` | `/api/students/{id}/enroll-face` | Admin | Enroll facial biometric template from multiple image captures. |
| `DELETE` | `/api/students/{id}/face-template`| Admin | Delete student's facial biometric template. |
| `POST` | `/api/recognition/identify` | Authenticated | Live webcam face identification and atomic attendance marking. |
| `GET` | `/api/attendance` | Admin | Query attendance records with multi-criteria filters. |
| `POST` | `/api/attendance/mark-manual` | Admin | Record manual attendance with proctor audit note. |
| `GET` | `/api/attendance/summary` | Admin | Turnout summary for a specific date. |
| `GET` | `/api/attendance/export` | Admin | Export sanitized CSV report. |

---

## 3. Endpoint Details

### `GET /api/health`
**Description**: Public system health check.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System health probe successful.",
  "data": {
    "status": "healthy",
    "service": "student-attendance-face-recognition",
    "server_time_utc": "2026-10-17T10:15:30.123456+00:00",
    "configured_timezone": "Asia/Kolkata",
    "database_backend": "cloud-firestore",
    "models": {
      "yunet_detector_loaded": true,
      "sface_recognizer_loaded": true,
      "similarity_threshold": 0.38,
      "match_margin": 0.08
    }
  }
}
```

---

### `POST /api/students`
**Description**: Registers a new student. Enforces unique `student_id`.

**Request Body**:
```json
{
  "student_id": "CS202601",
  "full_name": "Aarav Sharma",
  "department": "Computer Science",
  "year_of_study": 3,
  "email": "aarav.sharma@college.edu",
  "status": "active"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Student created successfully.",
  "data": {
    "student_id": "CS202601",
    "full_name": "Aarav Sharma",
    "department": "Computer Science",
    "year_of_study": 3,
    "email": "aarav.sharma@college.edu",
    "status": "active",
    "face_template": null,
    "enrollment_consent": false,
    "created_at": "2026-10-17T10:20:00Z",
    "updated_at": "2026-10-17T10:20:00Z"
  }
}
```

**Error (409 Conflict)**:
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_STUDENT_ID",
    "message": "Student with ID 'CS202601' already exists."
  }
}
```

---

### `POST /api/students/{student_id}/enroll-face`
**Description**: Extracts SFace embeddings from 1-5 captured frames, validates quality, averages vectors into a normalized template, and saves to the student record.

**Request Body**:
```json
{
  "images": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
  ],
  "consent": true
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Face template enrolled successfully for student 'CS202601'.",
  "data": {
    "student_id": "CS202601",
    "frames_accepted": 2,
    "frames_submitted": 2,
    "model_version": "sface_2021dec",
    "diagnostics": [
      {
        "frame": 1,
        "status": "ACCEPTED",
        "confidence": 0.942,
        "blur_score": 112.4
      },
      {
        "frame": 2,
        "status": "ACCEPTED",
        "confidence": 0.915,
        "blur_score": 98.6
      }
    ]
  }
}
```

---

### `POST /api/recognition/identify`
**Description**: Identifies a webcam frame against enrolled student templates and atomically marks attendance.

**Request Body**:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "session_id": "default",
  "mark_attendance": true
}
```

**Response (200 OK - Match & Attendance Recorded)**:
```json
{
  "success": true,
  "message": "Face identified successfully.",
  "data": {
    "result": "SUCCESS",
    "attendance_status": "marked",
    "student": {
      "student_id": "CS202601",
      "full_name": "Aarav Sharma",
      "department": "Computer Science"
    },
    "similarity_score": 0.8124,
    "confidence_margin": 0.4521,
    "bbox": { "x": 180, "y": 95, "w": 210, "h": 270 },
    "attendance_record": {
      "attendance_id": "att_CS202601_2026-10-17_default",
      "student_id": "CS202601",
      "attendance_date": "2026-10-17",
      "check_in_time": "15:45:10",
      "status": "present",
      "method": "face_recognition",
      "created_at": "2026-10-17T10:15:10Z"
    }
  }
}
```

**Response (200 OK - Ambiguous Match Flagged)**:
```json
{
  "success": true,
  "message": "Candidate ambiguity detected. Automatic attendance rejected for safety.",
  "data": {
    "result": "AMBIGUOUS_MATCH",
    "review_required": true,
    "similarity_score": 0.421,
    "confidence_margin": 0.021,
    "candidates": [
      { "student_id": "CS202601", "similarity": 0.421, "full_name": "Aarav Sharma" },
      { "student_id": "IT202603", "similarity": 0.400, "full_name": "Rohan Verma" }
    ]
  }
}
```

---

### `POST /api/attendance/mark-manual`
**Description**: Administrative manual attendance override.

**Request Body**:
```json
{
  "student_id": "CS202601",
  "date": "2026-10-17",
  "status": "present",
  "session_id": "default",
  "notes": "Medical certificate verified by Department Proctor"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Manual attendance recorded for student 'CS202601'.",
  "data": {
    "attendance_status": "marked",
    "record": {
      "attendance_id": "att_CS202601_2026-10-17_default",
      "student_id": "CS202601",
      "attendance_date": "2026-10-17",
      "status": "present",
      "method": "manual",
      "notes": "Medical certificate verified by Department Proctor"
    }
  }
}
```

---

### `GET /api/attendance/export`
**Description**: Streams a CSV export of attendance records with CSV formula injection sanitization.

**Query Parameters**:
- `date`: `YYYY-MM-DD`
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`
- `department`: string
- `student_id`: string

**Response**:
`Content-Type: text/csv`
```csv
Attendance ID,Student ID,Student Name,Department,Year,Date,Check-In Time,Status,Method,Session,Created By,Notes
att_CS202601_2026-10-17_default,CS202601,Aarav Sharma,Computer Science,3,2026-10-17,15:45:10,present,face_recognition,default,system,Automated kiosk match
```
