import React from 'react';

export default function CameraCapture({
  videoRef,
  isActive,
  error,
  devices = [],
  selectedDeviceId,
  onDeviceChange,
  onStart,
  onStop,
  onCapture,
  statusOverlay = null,
  guideClass = 'scanning',
  captureButtonLabel = 'Capture Frame',
  isProcessing = false,
}) {
  return (
    <div className="camera-card">
      <div className="camera-viewport">
        {isActive ? (
          <>
            <video
              ref={videoRef}
              className="camera-video"
              autoPlay
              playsInline
              muted
            />
            {/* Elliptical Face Alignment Target */}
            <div className={`face-target-guide ${guideClass}`} />

            {/* Status Pill Overlay */}
            {statusOverlay && (
              <div
                className="camera-overlay-status"
                style={{
                  backgroundColor: statusOverlay.bg || 'rgba(15, 23, 42, 0.85)',
                  color: statusOverlay.color || '#ffffff',
                }}
              >
                {statusOverlay.icon}
                <span>{statusOverlay.text}</span>
              </div>
            )}
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
            <svg
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ margin: '0 auto 1rem', display: 'block', opacity: 0.6 }}
            >
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <p style={{ fontWeight: 600, fontSize: '1.1rem', color: '#f8fafc' }}>Camera is Inactive</p>
            <p style={{ fontSize: '0.85rem', marginTop: '0.35rem' }}>
              Click "Start Camera" below to grant webcam permission.
            </p>
          </div>
        )}
      </div>

      {error && (
        <div
          style={{
            padding: '0.85rem 1.25rem',
            backgroundColor: 'var(--danger-light)',
            color: 'var(--danger)',
            fontSize: '0.85rem',
            borderTop: '1px solid var(--danger-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div
        style={{
          padding: '1rem 1.5rem',
          backgroundColor: '#ffffff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {devices.length > 1 && (
            <select
              className="form-control"
              style={{ width: 'auto', padding: '0.45rem 0.75rem', fontSize: '0.85rem' }}
              value={selectedDeviceId}
              onChange={(e) => onDeviceChange && onDeviceChange(e.target.value)}
              disabled={isActive}
            >
              {devices.map((device, idx) => (
                <option key={device.deviceId || idx} value={device.deviceId}>
                  {device.label || `Camera ${idx + 1}`}
                </option>
              ))}
            </select>
          )}

          {!isActive ? (
            <button onClick={onStart} className="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Camera
            </button>
          ) : (
            <button onClick={onStop} className="btn btn-secondary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="6" width="12" height="12" />
              </svg>
              Stop Camera
            </button>
          )}
        </div>

        {isActive && onCapture && (
          <button
            onClick={onCapture}
            className="btn btn-primary"
            disabled={isProcessing}
            style={{ minWidth: '150px' }}
          >
            {isProcessing ? 'Processing...' : captureButtonLabel}
          </button>
        )}
      </div>
    </div>
  );
}
