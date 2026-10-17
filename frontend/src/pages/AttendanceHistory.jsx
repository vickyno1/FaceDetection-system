import React, { useState, useEffect } from 'react';
import { attendanceAPI, studentsAPI } from '../api/apiClient';
import AttendanceTable from '../components/AttendanceTable';

export default function AttendanceHistory() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [filterMode, setFilterMode] = useState('single'); // 'single' or 'range'
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [department, setDepartment] = useState('');
  const [studentId, setStudentId] = useState('');
  const [status, setStatus] = useState('');

  // Manual Attendance Modal
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [manualForm, setManualForm] = useState({
    student_id: '',
    date: new Date().toISOString().split('T')[0],
    status: 'present',
    session_id: 'default',
    notes: 'Proctor manual verification',
  });
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterMode === 'single' && date) {
        params.date = date;
      } else if (filterMode === 'range') {
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
      }
      if (department) params.department = department;
      if (studentId) params.student_id = studentId;
      if (status) params.status = status;

      const res = await attendanceAPI.list(params);
      setRecords(res.data || []);
    } catch (err) {
      showNotice(err.message || 'Failed to fetch attendance records.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [filterMode, date, department, status]);

  // Load student list for manual modal
  useEffect(() => {
    async function loadStudents() {
      try {
        const res = await studentsAPI.list({ status: 'active' });
        setStudents(res.data || []);
      } catch (err) {
        console.error('Failed to load students:', err);
      }
    }
    loadStudents();
  }, []);

  const showNotice = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!manualForm.student_id) {
      showNotice('Please select a student.', 'danger');
      return;
    }
    setManualSubmitting(true);
    try {
      const res = await attendanceAPI.markManual(manualForm);
      showNotice(`Attendance recorded: ${res.data?.attendance_status || 'Success'}`);
      setIsManualModalOpen(false);
      fetchRecords();
    } catch (err) {
      showNotice(err.message || 'Failed to record manual attendance.', 'danger');
    } finally {
      setManualSubmitting(false);
    }
  };

  const handleExportCsv = () => {
    const params = {};
    if (filterMode === 'single' && date) params.date = date;
    if (filterMode === 'range') {
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
    }
    if (department) params.department = department;
    if (studentId) params.student_id = studentId;

    const url = attendanceAPI.exportCsvUrl(params);
    window.open(url, '_blank');
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance History & Audit Reports</h1>
          <p className="page-subtitle">
            Filter historical records, export sanitized CSV reports, and log administrative overrides
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => setIsManualModalOpen(true)} className="btn btn-secondary">
            + Manual Attendance Override
          </button>
          <button onClick={handleExportCsv} className="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export CSV
          </button>
        </div>
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

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ minWidth: '140px' }}>
            <label className="form-label">Query Mode</label>
            <select
              className="form-control"
              value={filterMode}
              onChange={(e) => setFilterMode(e.target.value)}
            >
              <option value="single">Single Date</option>
              <option value="range">Date Range</option>
            </select>
          </div>

          {filterMode === 'single' ? (
            <div style={{ minWidth: '160px' }}>
              <label className="form-label">Attendance Date</label>
              <input
                type="date"
                className="form-control"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
          ) : (
            <>
              <div style={{ minWidth: '150px' }}>
                <label className="form-label">Start Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div style={{ minWidth: '150px' }}>
                <label className="form-label">End Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </>
          )}

          <div style={{ minWidth: '180px' }}>
            <label className="form-label">Department</label>
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

          <div style={{ minWidth: '130px' }}>
            <label className="form-label">Status</label>
            <select
              className="form-control"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="present">Present</option>
              <option value="absent">Absent</option>
              <option value="late">Late</option>
            </select>
          </div>

          <div style={{ flex: '1', minWidth: '180px' }}>
            <label className="form-label">Student ID</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. CS202601"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value.toUpperCase())}
            />
          </div>

          <button onClick={fetchRecords} className="btn btn-secondary">
            Apply Filters
          </button>
        </div>
      </div>

      {/* Attendance Records Table */}
      <AttendanceTable
        records={records}
        isLoading={loading}
        emptyMessage="No attendance records match the selected date or criteria."
      />

      {/* Manual Attendance Override Modal */}
      {isManualModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Manual Attendance Override</h3>
              <button
                onClick={() => setIsManualModalOpen(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: '#64748b' }}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleManualSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Select Student *</label>
                  <select
                    className="form-control"
                    value={manualForm.student_id}
                    onChange={(e) => setManualForm({ ...manualForm, student_id: e.target.value })}
                  >
                    <option value="">-- Choose active student --</option>
                    {students.map((s) => (
                      <option key={s.student_id} value={s.student_id}>
                        {s.student_id} - {s.full_name} ({s.department})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Attendance Date *</label>
                  <input
                    type="date"
                    className="form-control"
                    value={manualForm.date}
                    onChange={(e) => setManualForm({ ...manualForm, date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Status *</label>
                  <select
                    className="form-control"
                    value={manualForm.status}
                    onChange={(e) => setManualForm({ ...manualForm, status: e.target.value })}
                  >
                    <option value="present">Present</option>
                    <option value="late">Late</option>
                    <option value="absent">Absent</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Audit Notes / Reason *</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Approved leave / Medical exemption / Proctor verification"
                    value={manualForm.notes}
                    onChange={(e) => setManualForm({ ...manualForm, notes: e.target.value })}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setIsManualModalOpen(false)}
                  className="btn btn-secondary"
                  disabled={manualSubmitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={manualSubmitting}>
                  {manualSubmitting ? 'Recording...' : 'Record Attendance'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
