# Contributing Guidelines

Thank you for your interest in contributing to the **Student Attendance Management System with Face Recognition**.

## Code of Conduct

All contributors and maintainers are expected to maintain a professional, respectful, and collaborative environment.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/student-attendance-face-recognition.git
   cd student-attendance-face-recognition
   ```

2. **Backend Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   python backend/models/download_models.py
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

4. **Running Tests**:
   Ensure all automated tests pass before submitting a Pull Request:
   ```bash
   python -m pytest backend/tests -v
   ```

## Coding Standards

- **Python**: Follow PEP 8 style guidelines. Ensure type hints and docstrings are maintained.
- **JavaScript / React**: Follow standard ES6+ conventions and functional React patterns with hooks.
- **Biometric Security**: Never store raw facial images directly in permanent database collections. Ensure all face embeddings are protected and direct client SDK access to biometric fields remains blocked.
- **CSV Security**: Always sanitize user-generated spreadsheet values with `sanitize_csv_cell` to avoid CSV formula injection (CWE-1236).

## Submitting Pull Requests

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Commit your changes with clear, descriptive commit messages.
3. Verify that all 20+ automated unit tests pass.
4. Push to your branch and open a Pull Request against `main`.
