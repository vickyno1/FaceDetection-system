import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login, loginDemo } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Failed to authenticate. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = () => {
    loginDemo();
    navigate(from, { replace: true });
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/logo.svg" alt="AttendFace Logo" />
          <h2 className="auth-title">AttendFace Admin</h2>
          <p className="auth-subtitle">Student Attendance & Face Recognition System</p>
        </div>

        {error && (
          <div
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: 'var(--danger-light)',
              color: 'var(--danger)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              marginBottom: '1.25rem',
              border: '1px solid var(--danger-border)',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Administrator Email</label>
            <input
              type="email"
              className="form-control"
              placeholder="admin@attendance.college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            {isSubmitting ? 'Authenticating...' : 'Sign In with Firebase'}
          </button>
        </form>

        <div style={{ position: 'relative', margin: '1.75rem 0', textAlign: 'center' }}>
          <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0' }} />
          <span
            style={{
              position: 'absolute',
              top: '-10px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#ffffff',
              padding: '0 0.75rem',
              fontSize: '0.75rem',
              color: '#94a3b8',
              fontWeight: 600,
              textTransform: 'uppercase',
            }}
          >
            Academic / Demo Evaluation
          </span>
        </div>

        <button
          type="button"
          onClick={handleDemoLogin}
          className="btn btn-secondary"
          style={{
            width: '100%',
            backgroundColor: '#f8fafc',
            border: '1px dashed #6366f1',
            color: '#4f46e5',
          }}
        >
          ⚡ Instant One-Click Admin Demo Login
        </button>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.78rem', color: '#64748b' }}>
          Protected via Firebase ID Token & OpenCV YuNet/SFace Backend Pipeline
        </div>
      </div>
    </div>
  );
}
