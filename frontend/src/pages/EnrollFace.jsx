import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { studentsAPI } from '../api/apiClient';
import { useCamera } from '../hooks/useCamera';
import CameraCapture from '../components/CameraCapture';
import LoadingSpinner from '../components/LoadingSpinner';

export default function EnrollFace() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState(searchParams.get('student_id') || '');
  const [consentGiven, setConsentGiven] = useState(false);

  // Multi-shot captures (array of base64 data URLs)
  const [capturedFrames, setCapturedFrames] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [enrollmentResult, setEnrollmentResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const {
    videoRef,
    isActive,
    error: cameraError,
    devices,
    selectedDeviceId,
    setSelectedDeviceId,
    startCamera,
    stopCamera,
    captureFrame,
  } = useCamera();

  // Load active students for dropdown
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

  const handleCaptureSample = () => {
    if (!consentGiven) {
      alert('You must accept the biometric consent notice before capturing facial data.');
      return;
    }
    const frame = captureFrame();
    if (frame) {
      if (capturedFrames.length < 5) {
        setCapturedFrames((prev) => [...prev, frame]);
      }
    }
  };

  const handleRemoveSample = (index) => {
    setCapturedFrames((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmitEnrollment = async () => {
    if (!selectedStudentId) {
      setErrorMessage('Please select a student.');
      return;
    }
    if (!consentGiven) {
      setErrorMessage('Explicit biometric consent is required.');
      return;
    }
    if (capturedFrames.length === 0) {
      setErrorMessage('Please capture at least 1-3 usable face frames.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setEnrollmentResult(null);

    try {
      const res = await studentsAPI.enrollFace(selectedStudentId, {
        images: capturedFrames,
        consent: consentGiven,
      });

      setEnrollmentResult(res.data);
      stopCamera();
    } catch (err) {
      setErrorMessage(err.message || 'Face enrollment failed.');
      if (err.details) {
        setEnrollmentResult({ diagnostics: err.details, success: false });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedStudent = students.find((s) => s.student_id === selectedStudentId);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Biometric Face Enrollment</h1>
          <p className="page-subtitle">
            Capture multiple calibrated facial angles for SFace 128-D embedding extraction
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: '2rem', alignItems: 'start' }}>
        {/* Left Column: Form & Consent */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
              1. Student Selection
            </h3>

            <div className="form-group">
              <label className="form-label">Select Student *</label>
              <select
                className="form-control"
                value={selectedStudentId}
                onChange={(e) => {
                  setSelectedStudentId(e.target.value);
                  setEnrollmentResult(null);
                  setErrorMessage(null);
                }}
              >
                <option value="">-- Choose active student --</option>
                {students.map((s) => (
                  <option key={s.student_id} value={s.student_id}>
                    {s.student_id} - {s.full_name} ({s.department}) {s.has_face_enrolled ? '[Has Template]' : ''}
                  </option>
                ))}
              </select>
            </div>

            {selectedStudent && (
              <div
                style={{
                  padding: '0.85rem',
                  backgroundColor: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <p><strong>Name:</strong> {selectedStudent.full_name}</p>
                <p><strong>Department:</strong> {selectedStudent.department}</p>
                <p>
                  <strong>Biometric Status:</strong>{' '}
                  {selectedStudent.has_face_enrolled ? (
                    <span style={{ color: 'var(--success)', fontWeight: 600 }}>Enrolled (SFace 128-D)</span>
                  ) : (
                    <span style={{ color: '#64748b' }}>Not yet enrolled</span>
                  )}
                </p>
              </div>
            )}
          </div>

          {/* Consent Banner */}
          <div
            className="card"
            style={{
              marginBottom: '1.5rem',
              borderLeft: '4px solid var(--warning)',
              backgroundColor: '#fffdf5',
            }}
          >
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#92400e', marginBottom: '0.5rem' }}>
              2. Biometric Consent & Limitation Notice
            </h3>
            <p style={{ fontSize: '0.82rem', color: '#78350f', lineHeight: 1.5, marginBottom: '0.85rem' }}>
              Under institutional privacy guidelines, raw webcam captures are processed locally to extract a
              128-dimensional mathematical feature vector and are not permanently retained as raw JPEG images.
              <strong> Security Notice:</strong> This system uses a standard 2D feature matcher (YuNet + SFace)
              without specialized active 3D IR or liveness hardware, making it vulnerable to photographs or screen
              replays.
            </p>

            <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={consentGiven}
                onChange={(e) => setConsentGiven(e.target.checked)}
                style={{ marginTop: '0.2rem' }}
              />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#92400e' }}>
                I confirm that documented student consent has been obtained for facial biometric enrollment.
              </span>
            </label>
          </div>

          {/* Captured Samples Strip */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
                3. Captured Samples ({capturedFrames.length} / 5)
              </h3>
              {capturedFrames.length > 0 && (
                <button
                  onClick={() => setCapturedFrames([])}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem' }}
                >
                  Clear All
                </button>
              )}
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Recommended: Capture 3-5 images with slight natural variations in head angle and room lighting for optimal recognition accuracy.
            </p>

            {capturedFrames.length === 0 ? (
              <div
                style={{
                  border: '2px dashed var(--border-strong)',
                  borderRadius: 'var(--radius-md)',
                  padding: '2rem',
                  textAlign: 'center',
                  color: '#94a3b8',
                  fontSize: '0.85rem',
                }}
              >
                No samples captured yet. Use the camera panel on the right.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                {capturedFrames.map((frame, idx) => (
                  <div
                    key={idx}
                    style={{
                      position: 'relative',
                      width: '90px',
                      height: '90px',
                      borderRadius: 'var(--radius-sm)',
                      overflow: 'hidden',
                      flexShrink: 0,
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <img src={frame} alt={`Sample ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    <button
                      onClick={() => handleRemoveSample(idx)}
                      style={{
                        position: 'absolute',
                        top: '2px',
                        right: '2px',
                        background: 'rgba(0,0,0,0.6)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '50%',
                        width: '18px',
                        height: '18px',
                        cursor: 'pointer',
                        fontSize: '11px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      &times;
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={handleSubmitEnrollment}
              className="btn btn-primary"
              disabled={isSubmitting || capturedFrames.length === 0 || !consentGiven || !selectedStudentId}
              style={{ width: '100%', marginTop: '1.25rem' }}
            >
              {isSubmitting ? 'Validating & Storing Template...' : 'Complete Face Enrollment'}
            </button>
          </div>
        </div>

        {/* Right Column: Camera Viewfinder & Result */}
        <div>
          <CameraCapture
            videoRef={videoRef}
            isActive={isActive}
            error={cameraError}
            devices={devices}
            selectedDeviceId={selectedDeviceId}
            onDeviceChange={setSelectedDeviceId}
            onStart={startCamera}
            onStop={stopCamera}
            onCapture={handleCaptureSample}
            captureButtonLabel={`Capture Sample (${capturedFrames.length + 1}/5)`}
            guideClass="scanning"
            statusOverlay={
              isActive
                ? {
                    text: `Align face inside guide • ${capturedFrames.length} captured`,
                    bg: 'rgba(15, 23, 42, 0.85)',
                    color: '#ffffff',
                  }
                : null
            }
          />

          {errorMessage && (
            <div
              style={{
                marginTop: '1.25rem',
                padding: '1rem',
                backgroundColor: 'var(--danger-light)',
                color: 'var(--danger)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem',
                border: '1px solid var(--danger-border)',
              }}
            >
              <strong>Error:</strong> {errorMessage}
            </div>
          )}

          {enrollmentResult && (
            <div
              className="card"
              style={{
                marginTop: '1.25rem',
                borderLeft: enrollmentResult.success !== false ? '4px solid var(--success)' : '4px solid var(--danger)',
              }}
            >
              <h3
                style={{
                  fontSize: '1.05rem',
                  fontWeight: 700,
                  color: enrollmentResult.success !== false ? 'var(--success)' : 'var(--danger)',
                  marginBottom: '0.5rem',
                }}
              >
                {enrollmentResult.success !== false ? '✓ Biometric Template Created!' : '✗ Quality Verification Failed'}
              </h3>

              {enrollmentResult.success !== false && (
                <p style={{ fontSize: '0.85rem', color: '#475569' }}>
                  Successfully aggregated <strong>{enrollmentResult.frames_accepted}</strong> valid face frames
                  into an SFace template. Student <strong>{enrollmentResult.student_id}</strong> is now ready
                  for live attendance recognition.
                </p>
              )}

              {enrollmentResult.diagnostics && (
                <div style={{ marginTop: '0.75rem' }}>
                  <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                    Frame Quality Diagnostics:
                  </p>
                  <ul style={{ fontSize: '0.78rem', paddingLeft: '1.25rem', color: '#475569' }}>
                    {enrollmentResult.diagnostics.map((d, i) => (
                      <li key={i} style={{ marginBottom: '0.2rem' }}>
                        Frame {d.frame}: <strong>{d.status}</strong> {d.reason ? `(${d.reason})` : `(Blur Score: ${d.blur_score})`}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
