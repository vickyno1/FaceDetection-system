import React from 'react';
import { formatDate, formatTime, getStatusBadgeClass } from '../utils/formatters';
import LoadingSpinner from './LoadingSpinner';

export default function AttendanceTable({ records = [], isLoading = false, emptyMessage = 'No attendance records found.' }) {
  if (isLoading) {
    return <LoadingSpinner message="Fetching attendance records..." />;
  }

  if (records.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem', color: '#64748b' }}>
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ margin: '0 auto 1rem', display: 'block', opacity: 0.5 }}
        >
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <p style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b' }}>{emptyMessage}</p>
        <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
          Mark attendance using Live Recognition or Manual Override.
        </p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>Student</th>
            <th>Department</th>
            <th>Date</th>
            <th>Check-in Time</th>
            <th>Method</th>
            <th>Status</th>
            <th>Proctor / Audit</th>
          </tr>
        </thead>
        <tbody>
          {records.map((rec) => (
            <tr key={rec.attendance_id || `${rec.student_id}-${rec.attendance_date}`}>
              <td>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {rec.full_name || rec.student_id}
                  </span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {rec.student_id}
                  </span>
                </div>
              </td>
              <td>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {rec.department || 'N/A'}
                </span>
              </td>
              <td>
                <span style={{ fontWeight: 500 }}>{formatDate(rec.attendance_date)}</span>
              </td>
              <td>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                  {formatTime(rec.check_in_time)}
                </span>
              </td>
              <td>
                <span
                  className={`badge ${
                    rec.method === 'face_recognition' ? 'badge-primary' : 'badge-neutral'
                  }`}
                  style={{ textTransform: 'capitalize' }}
                >
                  {rec.method === 'face_recognition' ? 'Face Match' : 'Manual Entry'}
                </span>
              </td>
              <td>
                <span className={`badge ${getStatusBadgeClass(rec.status)}`} style={{ textTransform: 'capitalize' }}>
                  {rec.status}
                </span>
              </td>
              <td>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.8rem', color: '#475569' }}>
                    {rec.created_by || 'system'}
                  </span>
                  {rec.notes && (
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic' }}>
                      {rec.notes}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
