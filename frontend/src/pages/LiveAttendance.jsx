import React, { useState, useEffect, useRef } from 'react';
import { recognitionAPI } from '../api/apiClient';
import { useCamera } from '../hooks/useCamera';
import CameraCapture from '../components/CameraCapture';
import { formatTime } from '../utils/formatters';

export default function LiveAttendance() {
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

  const [isProcessing, setIsProcessing] = useState(false);
  const [autoScan, setAutoScan] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  // Result state
  const [latestResult, setLatestResult] = useState(null);
  const [sessionLog, setSessionLog] = useState([]);
  const [statusMessage, setStatusMessage] = useState('Camera inactive. Press "Start Camera" to begin.');

  const scanTimerRef = useRef(null);

  // Perform frame capture and backend recognition
  const processFrame = async () => {
    if (isProcessing || !isActive) return;

    const frameB64 = captureFrame();
    if (!frameB64) return;

    setIsProcessing(true);
    setStatusMessage('Analyzing frame with YuNet & SFace...');

    try {
      const res = await recognitionAPI.identify({
        image: frameB64,
        session_id: 'default',
        mark_attendance: true,
      });

      const data = res.data;
      setLatestResult(data);

      if (data.result === 'SUCCESS') {
        const student = data.student;
        const attStatus = data.attendance_status;
        setStatusMessage(
          attStatus === 'marked'
            ? `✓ Marked Present: ${student.full_name} (${student.student_id})`
            : `ℹ Already Marked: ${student.full_name} (${student.student_id})`
        );

        // Append to current session log if not already present in the list
        setSessionLog((prev) => {
          const exists = prev.find((item) => item.student_id === student.student_id);
          if (!exists) {
            return [
              {
                student_id: student.student_id,
                full_name: student.full_name,
                department: student.department,
                time: new Date().toLocaleTimeString(),
                status: attStatus,
                score: data.similarity_score,
              },
              ...prev,
            ];
          }
          return prev;
        });
      } else if (data.result === 'AMBIGUOUS_MATCH') {
        setStatusMessage(`⚠ Ambiguous Match: Rejected. Top-2 candidates are too close.`);
      } else if (data.result === 'UNKNOWN_FACE') {
        setStatusMessage(`✗ Unknown Subject: Similarity below threshold (${data.similarity_score}).`);
      } else if (data.result === 'NO_FACE_DETECTED') {
        setStatusMessage('No face detected. Please stand in front of the camera.');
      } else if (data.result === 'MULTIPLE_FACES') {
        setStatusMessage('Multiple faces detected. Please scan one person at a time.');
      } else if (data.result === 'NO_ENROLLED_STUDENTS') {
        setStatusMessage('No enrolled students in the database. Please enroll students first.');
      } else {
        setStatusMessage(data.message || 'Face recognition unconfirmed.');
      }
    } catch (err) {
      setStatusMessage(`Error: ${err.message || 'Recognition request failed.'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Continuous Auto-Scan Interval
  useEffect(() => {
    if (isActive && autoScan) {
      scanTimerRef.current = setInterval(() => {
        processFrame();
      }, 2000); // 2-second scan interval
    } else {
      if (scanTimerRef.current) {
        clearInterval(scanTimerRef.current);
        scanTimerRef.current = null;
      }
    }

    return () => {
      if (scanTimerRef.current) {
        clearInterval(scanTimerRef.current);
      }
    };
  }, [isActive, autoScan, isProcessing]);

  // Determine guide styling and status banner colors
  let guideClass = 'scanning';
  let bannerBg = '#1e293b';
  let bannerColor = '#ffffff';

  if (latestResult?.result === 'SUCCESS') {
    guideClass = 'match';
    bannerBg = latestResult.attendance_status === 'marked' ? 'var(--success)' : 'var(--warning)';
    bannerColor = latestResult.attendance_status === 'marked' ? '#ffffff' : '#78350f';
  } else if (latestResult?.result === 'AMBIGUOUS_MATCH') {
    bannerBg = 'var(--warning)';
    bannerColor = '#78350f';
  } else if (latestResult?.result === 'UNKNOWN_FACE') {
    bannerBg = 'var(--danger)';
    bannerColor = '#ffffff';
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Attendance Kiosk</h1>
          <p className="page-subtitle">
            Automated facial recognition terminal powered by OpenCV YuNet detector and SFace recognizer
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={autoScan}
              onChange={(e) => setAutoScan(e.target.checked)}
              disabled={!isActive}
            />
            Auto-Scan Mode (2s)
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem', color: '#64748b' }}>
            <input
              type="checkbox"
              checked={showDebug}
              onChange={(e) => setShowDebug(e.target.checked)}
            />
            Telemetry / Debug
          </label>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2rem', alignItems: 'start' }}>
        {/* Left Column: Live Camera Viewfinder */}
        <div>
          <CameraCapture
            videoRef={videoRef}
            isActive={isActive}
            error={cameraError}
            devices={devices}
            selectedDeviceId={selectedDeviceId}
            onDeviceChange={setSelectedDeviceId}
            onStart={startCamera}
            onStop={() => {
              setAutoScan(false);
              stopCamera();
            }}
            onCapture={processFrame}
            isProcessing={isProcessing}
            captureButtonLabel="Scan Now"
            guideClass={guideClass}
            statusOverlay={
              isActive
                ? {
                    text: isProcessing ? 'Extracting features...' : statusMessage,
                    bg: bannerBg,
                    color: bannerColor,
                  }
                : null
            }
          />

          {/* Detailed Decision Card */}
          {latestResult && (
            <div
              className="card"
              style={{
                marginTop: '1.25rem',
                borderLeft: `4px solid ${
                  latestResult.result === 'SUCCESS'
                    ? 'var(--success)'
                    : latestResult.result === 'AMBIGUOUS_MATCH'
                    ? 'var(--warning)'
                    : 'var(--danger)'
                }`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span
                    className={`badge ${
                      latestResult.result === 'SUCCESS'
                        ? 'badge-success'
                        : latestResult.result === 'AMBIGUOUS_MATCH'
                        ? 'badge-warning'
                        : 'badge-danger'
                    }`}
                  >
                    {latestResult.result}
                  </span>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '0.4rem', color: 'var(--text-main)' }}>
                    {latestResult.student ? latestResult.student.full_name : 'No Match Confirmed'}
                  </h3>
                  {latestResult.student && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      ID: {latestResult.student.student_id} | {latestResult.student.department}
                    </p>
                  )}
                </div>

                {latestResult.attendance_status && (
                  <span
                    className={`badge ${
                      latestResult.attendance_status === 'marked' ? 'badge-success' : 'badge-warning'
                    }`}
                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
                  >
                    Attendance: {latestResult.attendance_status.toUpperCase()}
                  </span>
                )}
              </div>

              {/* Debug Telemetry */}
              {showDebug && (
                <div
                  style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: '#0f172a',
                    color: '#38bdf8',
                    borderRadius: 'var(--radius-sm)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                  }}
                >
                  <p><strong>Similarity Score:</strong> {latestResult.similarity_score ?? 'N/A'}</p>
                  <p><strong>Confidence Margin:</strong> {latestResult.confidence_margin ?? 'N/A'}</p>
                  {latestResult.candidates && latestResult.candidates.length > 0 && (
                    <div style={{ marginTop: '0.35rem' }}>
                      <p style={{ color: '#94a3b8' }}>Top Candidates:</p>
                      {latestResult.candidates.map((c, i) => (
                        <p key={i} style={{ paddingLeft: '0.5rem' }}>
                          #{i + 1}: {c.student_id} ({c.similarity}) - {c.full_name}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Live Session Log */}
        <div>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Active Terminal Log</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {sessionLog.length} students processed in this session
                </p>
              </div>

              {sessionLog.length > 0 && (
                <button
                  onClick={() => setSessionLog([])}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem' }}
                >
                  Reset Log
                </button>
              )}
            </div>

            {sessionLog.length === 0 ? (
              <div
                style={{
                  padding: '3rem 1rem',
                  textAlign: 'center',
                  color: '#94a3b8',
                  fontSize: '0.85rem',
                  border: '1px dashed var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                No attendance scans recorded during this session yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', maxHeight: '420px', overflowY: 'auto' }}>
                {sessionLog.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 1rem',
                      backgroundColor: '#f8fafc',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div>
                      <p style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                        {item.full_name}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {item.student_id} • {item.department}
                      </p>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <span
                        className={`badge ${
                          item.status === 'marked' ? 'badge-success' : 'badge-warning'
                        }`}
                        style={{ fontSize: '0.7rem' }}
                      >
                        {item.status === 'marked' ? 'Marked' : 'Already Marked'}
                      </span>
                      <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
                        {item.time}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
