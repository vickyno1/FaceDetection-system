import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { studentsAPI, attendanceAPI } from '../api/apiClient';
import StudentForm from '../components/StudentForm';
import LoadingSpinner from '../components/LoadingSpinner';
import AttendanceTable from '../components/AttendanceTable';

export default function Students() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [status, setStatus] = useState('');

  // Modal states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // History Drawer / Modal state
  const [selectedStudentForHistory, setSelectedStudentForHistory] = useState(null);
  const [studentHistoryRecords, setStudentHistoryRecords] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [notification, setNotification] = useState(null);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const params = {};
      if (search) params.q = search;
      if (department) params.department = department;
      if (status) params.status = status;

      const res = await studentsAPI.list(params);
      setStudents(res.data || []);
    } catch (err) {
      showNotice(err.message || 'Failed to fetch students.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [department, status]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchStudents();
  };

  const showNotice = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleCreateOrUpdate = async (formData) => {
    setIsSubmitting(true);
    try {
      if (editingStudent) {
        await studentsAPI.update(editingStudent.student_id, formData);
        showNotice(`Student '${editingStudent.student_id}' updated successfully.`);
      } else {
        await studentsAPI.create(formData);
        showNotice(`Student '${formData.student_id}' created successfully.`);
      }
      setIsFormOpen(false);
      setEditingStudent(null);
      fetchStudents();
    } catch (err) {
      showNotice(err.message || 'Operation failed.', 'danger');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeactivate = async (studentId) => {
    if (!window.confirm(`Are you sure you want to deactivate student '${studentId}'?`)) {
      return;
    }
    try {
      await studentsAPI.deactivate(studentId);
      showNotice(`Student '${studentId}' deactivated.`);
      fetchStudents();
    } catch (err) {
      showNotice(err.message || 'Failed to deactivate student.', 'danger');
    }
  };

  const handleDeleteFace = async (studentId) => {
    if (!window.confirm(`Delete facial biometric template for student '${studentId}'? This action cannot be undone.`)) {
      return;
    }
    try {
      await studentsAPI.deleteFaceTemplate(studentId);
      showNotice(`Biometric template deleted for '${studentId}'.`);
      fetchStudents();
    } catch (err) {
      showNotice(err.message || 'Failed to delete template.', 'danger');
    }
  };

  const handleViewHistory = async (student) => {
    setSelectedStudentForHistory(student);
    setHistoryLoading(true);
    try {
      const res = await attendanceAPI.list({ student_id: student.student_id });
      setStudentHistoryRecords(res.data || []);
    } catch (err) {
      showNotice(err.message || 'Failed to load student attendance history.', 'danger');
    } finally {
      setHistoryLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Student Directory</h1>
          <p className="page-subtitle">Manage student enrollment, departments, and facial biometric status</p>
        </div>

        <button
          onClick={() => {
            setEditingStudent(null);
            setIsFormOpen(true);
          }}
          className="btn btn-primary"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Register New Student
        </button>
      </div>

      {notification && (
        <div
          style={{
            padding: '0.85rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            backgroundColor: notification.type === 'danger' ? 'var(--danger-light)' : 'var(--success-light)',
            color: notification.type === 'danger' ? 'var(--danger)' : 'var(--success)',
            border: `1px solid ${notification.type === 'danger' ? 'var(--danger-border)' : 'var(--success-border)'}`,
            fontWeight: 500,
          }}
        >
          {notification.msg}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '2', minWidth: '220px' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search by student ID or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ flex: '1', minWidth: '180px' }}>
            <select
              className="form-control"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              <option value="">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Data Science">Data Science</option>
              <option value="Artificial Intelligence">Artificial Intelligence</option>
              <option value="Electronics & Communication">Electronics & Communication</option>
              <option value="Mechanical Engineering">Mechanical Engineering</option>
            </select>
          </div>

          <div style={{ flex: '1', minWidth: '130px' }}>
            <select
              className="form-control"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <button type="submit" className="btn btn-secondary">
            Search
          </button>
        </form>
      </div>

      {/* Students Table */}
      {loading ? (
        <LoadingSpinner message="Loading students..." />
      ) : students.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem' }}>
          <p style={{ fontWeight: 600, fontSize: '1rem', color: '#64748b' }}>No students found matching your criteria.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Full Name</th>
                <th>Department</th>
                <th>Year</th>
                <th>Status</th>
                <th>Face Biometrics</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{s.student_id}</td>
                  <td style={{ fontWeight: 600 }}>{s.full_name}</td>
                  <td>{s.department}</td>
                  <td>Year {s.year_of_study}</td>
                  <td>
                    <span className={`badge ${s.status === 'active' ? 'badge-success' : 'badge-danger'}`}>
                      {s.status}
                    </span>
                  </td>
                  <td>
                    {s.has_face_enrolled ? (
                      <span className="badge badge-primary" title="SFace 128-D embedding stored">
                        ✓ Enrolled
                      </span>
                    ) : (
                      <span className="badge badge-neutral">Not Enrolled</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => handleViewHistory(s)}
                        className="btn btn-secondary btn-sm"
                        title="View Attendance History"
                      >
                        History
                      </button>

                      <button
                        onClick={() => {
                          setEditingStudent(s);
                          setIsFormOpen(true);
                        }}
                        className="btn btn-secondary btn-sm"
                        title="Edit Details"
                      >
                        Edit
                      </button>

                      <Link
                        to={`/enroll-face?student_id=${s.student_id}`}
                        className="btn btn-primary btn-sm"
                        title="Enroll or Re-enroll Face"
                      >
                        {s.has_face_enrolled ? 'Re-enroll' : 'Enroll Face'}
                      </Link>

                      {s.has_face_enrolled && (
                        <button
                          onClick={() => handleDeleteFace(s.student_id)}
                          className="btn btn-secondary btn-sm"
                          style={{ color: 'var(--danger)', borderColor: 'var(--danger-border)' }}
                          title="Delete Biometric Template"
                        >
                          Clear Face
                        </button>
                      )}

                      {s.status === 'active' && (
                        <button
                          onClick={() => handleDeactivate(s.student_id)}
                          className="btn btn-secondary btn-sm"
                          style={{ color: '#64748b' }}
                          title="Deactivate Student"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Registration / Edit Modal */}
      <StudentForm
        isOpen={isFormOpen}
        student={editingStudent}
        onClose={() => {
          setIsFormOpen(false);
          setEditingStudent(null);
        }}
        onSubmit={handleCreateOrUpdate}
        isSubmitting={isSubmitting}
      />

      {/* Student Attendance History Modal */}
      {selectedStudentForHistory && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '800px' }}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Attendance History: {selectedStudentForHistory.full_name}</h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  ID: {selectedStudentForHistory.student_id} | {selectedStudentForHistory.department}
                </p>
              </div>
              <button
                onClick={() => setSelectedStudentForHistory(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: '#64748b' }}
              >
                &times;
              </button>
            </div>

            <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              <AttendanceTable
                records={studentHistoryRecords}
                isLoading={historyLoading}
                emptyMessage={`No attendance records found for ${selectedStudentForHistory.full_name}.`}
              />
            </div>

            <div className="modal-footer">
              <button
                type="button"
                onClick={() => setSelectedStudentForHistory(null)}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
