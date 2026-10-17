# Cloud Firestore Database Schema & Data Dictionary

This document specifies the database collections, document structures, constraints, and indexing configuration for the **Student Attendance Management System**.

---

## 1. Collections Architecture

The database utilizes Cloud Firestore NoSQL document store with three primary collections:
1. `students`: Master student registry and protected biometric feature vectors.
2. `attendance`: Authoritative attendance check-in records.
3. `audit_logs`: Immutable security audit trail of administrative modifications.

---

## 2. Collection: `students`

### Document ID:
Normalized uppercase `student_id` (e.g., `CS202601`).

### Schema:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `student_id` | String | Yes | Unique alphanumeric student ID / Roll No (2-30 chars). |
| `full_name` | String | Yes | Full legal name of student (2-100 chars). |
| `department` | String | Yes | Academic department (e.g. "Computer Science"). |
| `year_of_study` | Integer | Yes | Current year of study (1 to 8). |
| `email` | String | No | Institutional email address. |
| `status` | String | Yes | `active` or `inactive`. Inactive students are ignored during live face scans. |
| `face_template` | Array&lt;Float&gt; | No | 128-dimensional L2-normalized SFace embedding vector. |
| `face_model_version` | String | No | Model descriptor (e.g. `sface_2021dec`). |
| `enrollment_consent` | Boolean | Yes | Documented consent confirmation flag. |
| `created_at` | String (ISO) | Yes | UTC timestamp of registration. |
| `updated_at` | String (ISO) | Yes | UTC timestamp of last modification. |

### Security Policy:
- Direct client reads of `face_template` are explicitly blocked via Firestore Security Rules.
- Client SDK creation/updates are denied; all mutations require backend server verification.

---

## 3. Collection: `attendance`

### Document ID:
Deterministic compound key:
$$\texttt{att\_\{student\_id\}\_\{attendance\_date\}\_\{session\_id\}}$$
*Example*: `att_CS202601_2026-10-17_default`

### Schema:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `attendance_id` | String | Yes | Matches the document ID. |
| `student_id` | String | Yes | Reference to student. |
| `attendance_date` | String | Yes | Date formatted as `YYYY-MM-DD` in configured timezone (`Asia/Kolkata`). |
| `check_in_time` | String | Yes | Timestamp formatted as `HH:MM:SS` in configured timezone. |
| `status` | String | Yes | `present`, `absent`, or `late`. |
| `method` | String | Yes | `face_recognition` or `manual`. |
| `session_id` | String | Yes | Academic period or lecture session (`default` for daily attendance). |
| `created_at` | String (ISO) | Yes | ISO 8601 UTC timestamp. |
| `created_by` | String | Yes | Firebase UID of administrator or `system`. |
| `notes` | String | No | Proctor remarks or override justification. |

---

## 4. Collection: `audit_logs`

### Document ID:
Auto-generated Firestore UUID.

### Schema:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `actor_uid` | String | Yes | Firebase user UID who initiated the action. |
| `action` | String | Yes | Enum: `STUDENT_CREATED`, `STUDENT_UPDATED`, `STUDENT_DEACTIVATED`, `FACE_TEMPLATE_ENROLLED`, `FACE_TEMPLATE_DELETED`, `ATTENDANCE_MARKED`. |
| `target_type` | String | Yes | `student` or `attendance`. |
| `target_id` | String | Yes | ID of affected entity. |
| `timestamp` | String (ISO) | Yes | ISO 8601 UTC timestamp. |
| `sanitized_metadata`| Map | No | Contextual metadata (excluding sensitive vectors or credentials). |

---

## 5. Composite Indexes

As defined in `firestore.indexes.json`:
1. `attendance`: `attendance_date` (DESC) + `check_in_time` (DESC)
2. `attendance`: `student_id` (ASC) + `attendance_date` (DESC)
3. `attendance`: `status` (ASC) + `attendance_date` (DESC)
4. `students`: `department` (ASC) + `status` (ASC)
