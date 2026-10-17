import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { attendanceAPI } from '../api/apiClient';
import AttendanceTable from '../components/AttendanceTable';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await attendanceAPI.getDashboard();
      setData(res.data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Calculating attendance metrics from database..." />;
  }

  if (error) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', fontWeight: 600 }}>{error}</p>
        <button onClick={fetchDashboard} className="btn btn-secondary btn-sm" style={{ marginTop: '1rem' }}>
          Retry
        </button>
      </div>
    );
  }

  const summary = data?.summary || {
    total_active_students: 0,
    present_today: 0,
    not_marked_today: 0,
    attendance_rate_percent: 0,
  };

  const trend = data?.trend || [];
  const recent = data?.recent_check_ins || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Executive Dashboard</h1>
          <p className="page-subtitle">Real-time attendance overview & computer vision telemetry</p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/live-attendance" className="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Launch Live Kiosk
          </Link>
          <Link to="/history" className="btn btn-secondary">
            View Reports
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="card metric-card">
          <div>
            <p className="metric-title">Total Active Students</p>
            <p className="metric-value">{summary.total_active_students}</p>
            <p className="metric-desc">{data?.enrolled_faces_count || 0} students face-enrolled</p>
          </div>
          <div className="metric-icon-box" style={{ backgroundColor: '#eef2ff', color: '#4f46e5' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
        </div>

        <div className="card metric-card">
          <div>
            <p className="metric-title">Present Today</p>
            <p className="metric-value" style={{ color: 'var(--success)' }}>
              {summary.present_today}
            </p>
            <p className="metric-desc">Verified check-ins today</p>
          </div>
          <div className="metric-icon-box" style={{ backgroundColor: '#ecfdf5', color: '#10b981' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
        </div>

        <div className="card metric-card">
          <div>
            <p className="metric-title">Not Yet Marked</p>
            <p className="metric-value" style={{ color: 'var(--danger)' }}>
              {summary.not_marked_today}
            </p>
            <p className="metric-desc">Pending check-in or absent</p>
          </div>
          <div className="metric-icon-box" style={{ backgroundColor: '#fef2f2', color: '#ef4444' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
        </div>

        <div className="card metric-card">
          <div>
            <p className="metric-title">Attendance Rate</p>
            <p className="metric-value">{summary.attendance_rate_percent}%</p>
            <p className="metric-desc">Turnout for {summary.date || 'today'}</p>
          </div>
          <div className="metric-icon-box" style={{ backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </div>
        </div>
      </div>

      {/* 7-Day Attendance Trend Bar Chart */}
      <div className="trend-chart-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              7-Day Attendance Trend
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Historical turnout computed across stored dates
            </p>
          </div>
          <span className="badge badge-primary">Dynamic Database Query</span>
        </div>

        <div className="chart-bars-container">
          {trend.map((day) => {
            const heightPercent = Math.min(100, Math.max(5, day.percentage));
            return (
              <div key={day.date} className="chart-bar-group">
                <div className="chart-bar" style={{ height: `${heightPercent}%` }}>
                  <div className="chart-bar-tooltip">
                    {day.present} present ({day.percentage}%)
                  </div>
                </div>
                <span className="chart-label">{day.day_label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Check-Ins */}
      <div style={{ marginTop: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Today's Recent Check-Ins</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Latest recognized or manually logged attendance entries
            </p>
          </div>
          <Link to="/history" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)' }}>
            View Full Records &rarr;
          </Link>
        </div>

        <AttendanceTable
          records={recent}
          emptyMessage="No students have checked in yet today."
        />
      </div>
    </div>
  );
}
