# Student Attendance Management System with Face Recognition

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![OpenCV](https://img.shields.io/badge/OpenCV-YuNet%20%2B%20SFace-green.svg)](https://opencv.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth%20%2B%20Firestore-orange.svg)](https://firebase.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An institutional-grade, full-stack biometric attendance management system. The application identifies registered students through a webcam stream using **OpenCV YuNet** (face detection) and **OpenCV SFace** (128-D facial feature recognition), preventing duplicate attendance entries, enforcing biometric consent, and recording authoritative attendance in **Google Cloud Firestore**.

---

## Key Features

- **Decoupled Face Recognition Pipeline**: Separates lightweight, high-performance face detection (YuNet) from metric face recognition (SFace). Raw webcam photos are discarded immediately after in-memory feature extraction; only normalized 128-D templates are retained.
- **Configurable Cosine Matching & Ambiguity Rejection**: Calibrated cosine similarity threshold ($\theta_{\text{sim}} = 0.380$) combined with a candidate ambiguity check ($\delta_{\text{margin}} \ge 0.080$). If the top two enrolled candidates are too close, automatic attendance is rejected for administrative review.
- **Atomic Idempotency & Duplicate Prevention**: Prevents duplicate attendance writes under concurrent network requests using deterministic Firestore document keys (`att_{student_id}_{attendance_date}_{session_id}`) and mutex locks.
- **Role-Based Security**: Server-side Firebase ID token verification protects administrative student management, face enrollment, and report queries. Direct client SDK access to biometric fields is denied via Firestore Security Rules.
- **Sanitized CSV Reports**: Automatically escapes dangerous spreadsheet formula prefixes (`=`, `+`, `-`, `@`) to protect against CSV Formula Injection (CWE-1236).
- **Proctored Manual Override**: Allows administrators to record manual check-ins with an audit trail when face recognition fails or during medical leave.
- **Dual-Mode Engine**: Operates in **Full Firebase Cloud Mode** or **Zero-Config In-Memory Mode**, allowing complete portfolio reviews and automated testing without configuring cloud credentials first.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, React Router 6, Axios, Browser MediaDevices API, Firebase Web SDK |
| **Backend** | Python 3.11+, Flask, Flask-CORS, Firebase Admin SDK, OpenCV DNN, NumPy |
| **Face Detection** | OpenCV YuNet (`face_detection_yunet_2023mar.onnx`) |
| **Face Recognition** | OpenCV SFace (`face_recognition_sface_2021dec.onnx`) |
| **Database & Auth** | Google Cloud Firestore, Firebase Authentication |
| **Testing** | Pytest (20 automated unit & concurrency tests) |

---

## Directory Structure

```
student-attendance-face-recognition/
├── frontend/
│   ├── public/
│   │   ├── favicon.ico
│   │   └── logo.svg
│   ├── src/
│   │   ├── api/
│   │   │   └── apiClient.js             # Centralized Axios client & auth interceptor
│   │   ├── components/
│   │   │   ├── Navbar.jsx               # Header with proctor profile & timezone
│   │   │   ├── Sidebar.jsx              # Navigation menu
│   │   │   ├── ProtectedRoute.jsx       # Route guard for authenticated admin
│   │   │   ├── StudentForm.jsx          # Validated student registration form modal
│   │   │   ├── CameraCapture.jsx        # Viewfinder, device selector & oval guide
│   │   │   ├── AttendanceTable.jsx      # Sortable, paginated attendance log
│   │   │   └── LoadingSpinner.jsx       # Loading indicator
│   │   ├── pages/
│   │   │   ├── Login.jsx                # Firebase Auth & One-Click Demo login
│   │   │   ├── Dashboard.jsx            # Dynamic turnout metrics & 7-day trend chart
│   │   │   ├── Students.jsx             # Student CRUD directory
│   │   │   ├── EnrollFace.jsx           # Multi-frame face capture & template aggregation
│   │   │   ├── LiveAttendance.jsx       # Real-time kiosk scanner & session log
│   │   │   ├── AttendanceHistory.jsx    # Date filters, manual override & CSV export
│   │   │   └── NotFound.jsx             # 404 handler
│   │   ├── context/
│   │   │   └── AuthContext.jsx          # Firebase auth session provider
│   │   ├── hooks/
│   │   │   └── useCamera.js             # MediaDevices webcam hook
│   │   ├── utils/
│   │   │   └── formatters.js            # Date, time, and badge formatters
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css                   # Custom responsive design system
│   ├── index.html
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── __init__.py                  # Flask application factory
│   │   ├── config.py                    # Environment configuration
│   │   ├── extensions.py                # Service singletons & dependency injection
│   │   ├── routes/
│   │   │   ├── health.py                # Liveness & model diagnostics probe
│   │   │   ├── students.py              # Student management & enrollment endpoints
│   │   │   ├── recognition.py           # Face identification route
│   │   │   └── attendance.py            # Dashboard metrics & CSV export
│   │   ├── services/
│   │   │   ├── face_detector.py         # YuNet wrapper & blur/quality validation
│   │   │   ├── face_recognizer.py       # SFace wrapper & cosine ambiguity logic
│   │   │   ├── student_service.py       # Student domain logic
│   │   │   └── attendance_service.py    # Authoritative attendance recording
│   │   ├── repositories/
│   │   │   ├── student_repository.py    # Firestore & In-Memory student storage
│   │   │   └── attendance_repository.py # Atomic attendance repository
│   │   ├── middleware/
│   │   │   └── auth.py                  # Server-side Firebase ID token verification
│   │   └── utils/
│   │       ├── validators.py            # Input validation & CSV formula sanitizer
│   │       └── responses.py             # Standardized JSON response formatting
│   ├── models/
│   │   ├── README.md                    # Official ONNX source URLs & verification
│   │   ├── download_models.py           # Automated model downloader
│   │   ├── face_detection_yunet_2023mar.onnx
│   │   └── face_recognition_sface_2021dec.onnx
│   ├── scripts/
│   │   └── seed_demo_data.py            # Demo students, biometrics & attendance seeder
│   ├── tests/
│   │   ├── conftest.py                  # Pytest fixtures & mock tokens
│   │   ├── test_health.py               # Liveness probe tests
│   │   ├── test_validation.py           # Schema & CSV injection tests
│   │   ├── test_recognition.py          # Vector math & ambiguity tests
│   │   └── test_attendance.py           # Idempotency & concurrency tests
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── docs/
│   ├── architecture.md                  # Architecture diagrams & threat analysis
│   ├── api.md                           # REST API specification
│   ├── database-schema.md               # Firestore schemas & indexes
│   └── testing.md                       # QA strategy & test execution guide
├── firestore.rules                      # Cloud Firestore security rules
├── firestore.indexes.json               # Firestore composite index definitions
├── .gitignore
├── .gitattributes
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

---

## Quick Start Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed
- A standard USB or built-in webcam

---

### 2. Backend Setup

1. Open your terminal and navigate to the project directory:
   ```bash
   cd student-attendance-face-recognition
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Download the official OpenCV YuNet and SFace ONNX models:
   ```bash
   python backend/models/download_models.py
   ```

4. Populate realistic demonstration students, biometric templates, and 7-day attendance records:
   ```bash
   python backend/scripts/seed_demo_data.py
   ```

5. Run the automated Pytest suite (20 tests):
   ```bash
   python -m pytest backend/tests -v
   ```

6. Start the Flask backend server:
   ```bash
   python backend/run.py
   ```
   *The server starts on `http://localhost:5000`.*

---

### 3. Frontend Setup

1. Open a second terminal window and navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The client opens on `http://localhost:5173`.*

---

### 4. Running the Application

1. Open `http://localhost:5173` in your browser.
2. Click **⚡ Instant One-Click Admin Demo Login** to enter the administrative dashboard.
3. Explore the features:
   - **Dashboard**: View live turnout statistics, 7-day trend chart, and today's check-ins.
   - **Student Directory**: Add, search, and edit students, or view their attendance history.
   - **Face Enrollment**: Select an active student, grant webcam permission, review the biometric consent notice, capture 3-5 facial angles, and save their template.
   - **Live Attendance**: Start the live kiosk, activate **Auto-Scan Mode (2s)**, stand in front of the camera, and watch attendance get recorded with green visual confirmation and timestamping.
   - **Attendance History**: Filter records by date or department, record manual proctor overrides, and export sanitized CSV reports.

---

## Configuration & Environment Variables

Copy the `.env.example` templates to `.env` in both folders:

### Backend Configuration (`backend/.env`):
```ini
FLASK_ENV=development
PORT=5000
FRONTEND_ORIGIN=http://localhost:5173

# Set to 'false' in production with real Firebase service account
MOCK_FIREBASE=true
FIREBASE_PROJECT_ID=your-firebase-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccountKey.json

# Computer Vision Calibration
FACE_SIMILARITY_THRESHOLD=0.380
FACE_MATCH_MARGIN=0.080
FACE_MIN_SIZE=60
FACE_DETECTION_CONFIDENCE=0.80

# Timezone Policy (defaults to Asia/Kolkata)
ATTENDANCE_TIMEZONE=Asia/Kolkata
```

### Frontend Configuration (`frontend/.env`):
```ini
VITE_API_BASE_URL=/api
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=1:1234567890:web:abcdef
```

---

## Biometric Privacy & Security Policy

1. **No Raw Image Retention**: Images captured by the camera are used only in memory during the detection and embedding extraction step. No raw student photos are stored in the database.
2. **Explicit Consent**: Face enrollment strictly enforces documented student consent (`enrollment_consent = true`).
3. **Biometric Deletion**: Administrators can purge biometric vectors at any time via the UI or `DELETE /api/students/{id}/face-template`.
4. **2D Matching Limitations**: Standard 2D face recognition using RGB webcams is vulnerable to presentation attacks (e.g., displaying a photo on a smartphone). The system is intended for proctored kiosks with supervisor oversight.

---

## License

This project is licensed under the [MIT License](LICENSE).
