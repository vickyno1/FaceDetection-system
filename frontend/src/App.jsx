import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import EnrollFace from './pages/EnrollFace';
import LiveAttendance from './pages/LiveAttendance';
import AttendanceHistory from './pages/AttendanceHistory';
import NotFound from './pages/NotFound';

function Layout({ children, title }) {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-layout">
        <Navbar title={title} />
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  const location = useLocation();

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/dashboard':
        return 'Overview Dashboard';
      case '/students':
        return 'Student Directory';
      case '/enroll-face':
        return 'Facial Biometric Enrollment';
      case '/live-attendance':
        return 'Live Attendance Terminal';
      case '/history':
        return 'Attendance History & Audit';
      default:
        return 'Attendance Portal';
    }
  };

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={<Navigate to="/dashboard" replace />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout title={getPageTitle(location.pathname)}>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/students"
        element={
          <ProtectedRoute>
            <Layout title={getPageTitle(location.pathname)}>
              <Students />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/enroll-face"
        element={
          <ProtectedRoute>
            <Layout title={getPageTitle(location.pathname)}>
              <EnrollFace />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/live-attendance"
        element={
          <ProtectedRoute>
            <Layout title={getPageTitle(location.pathname)}>
              <LiveAttendance />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <Layout title={getPageTitle(location.pathname)}>
              <AttendanceHistory />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
