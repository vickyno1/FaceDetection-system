import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ title = 'Attendance Portal' }) {
  const { user, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="navbar-left">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>{title}</h2>
        <span className="badge badge-info" style={{ marginLeft: '0.5rem' }}>
          IST (Asia/Kolkata)
        </span>
      </div>

      <div className="navbar-right">
        {user && (
          <>
            <div className="user-profile">
              <div className="user-avatar">
                {user.displayName ? user.displayName.charAt(0).toUpperCase() : 'A'}
              </div>
              <div className="user-info">
                <span className="user-name">{user.displayName || 'Administrator'}</span>
                <span className="user-role">{user.email || 'Admin'}</span>
              </div>
            </div>

            <button
              onClick={logout}
              className="btn btn-secondary btn-sm"
              title="Sign Out"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
}
