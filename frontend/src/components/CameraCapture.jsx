import React, { useRef, useState, useEffect, useCallback } from 'react'

/**
 * CameraCapture
 * Props:
 *   onCapture(file: File)  — called when user confirms a photo
 *   onClose()              — called when user closes the camera
 *
 * Notes:
 *   • Camera access requires HTTPS or localhost (browser security requirement).
 *   • The rear camera is preferred on phones (facingMode: 'environment').
 *   • Front/rear switching is offered when the browser reports multiple cameras.
 *   • All MediaStream tracks are stopped when the component unmounts or the
 *     user closes the camera.
 */

const CONSTRAINTS_REAR  = { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false }
const CONSTRAINTS_FRONT = { video: { facingMode: { ideal: 'user'        }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false }

export default function CameraCapture({ onCapture, onClose }) {
  const videoRef   = useRef(null)
  const canvasRef  = useRef(null)
  const streamRef  = useRef(null)

  const [phase, setPhase]             = useState('starting')  // starting | live | captured | error
  const [errorMsg, setErrorMsg]       = useState('')
  const [capturedDataUrl, setCapturedDataUrl] = useState(null)
  const [facingMode, setFacingMode]   = useState('rear')      // 'rear' | 'front'
  const [canSwitch, setCanSwitch]     = useState(false)

  // ---- Stop all camera tracks ------------------------------------------
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
  }, [])

  // ---- Start camera -------------------------------------------------------
  const startCamera = useCallback(async (mode = 'rear') => {
    stopStream()
    setPhase('starting')
    setErrorMsg('')
    setCapturedDataUrl(null)

    const constraints = mode === 'rear' ? CONSTRAINTS_REAR : CONSTRAINTS_FRONT

    try {
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setPhase('live')

      // Check if device has multiple cameras for the switch button
      const devices = await navigator.mediaDevices.enumerateDevices()
      const videoDevices = devices.filter(d => d.kind === 'videoinput')
      setCanSwitch(videoDevices.length > 1)
    } catch (err) {
      stopStream()
      setPhase('error')
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMsg(
          'Camera permission was denied. Please allow camera access in your browser settings, then try again.'
        )
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMsg(
          'No camera was found on this device. Please use the "Upload Image" option instead.'
        )
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setErrorMsg(
          'Camera is in use by another application. Close other apps using the camera, then try again.'
        )
      } else if (err.name === 'OverconstrainedError') {
        // Retry without specific facingMode constraint
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
          streamRef.current = stream
          if (videoRef.current) videoRef.current.srcObject = stream
          setPhase('live')
        } catch {
          setErrorMsg(`Could not access camera: ${err.message}`)
        }
      } else if (!window.isSecureContext) {
        setErrorMsg(
          'Camera access requires HTTPS or localhost. ' +
          'Please open the app over HTTPS, or test on localhost.'
        )
      } else {
        setErrorMsg(`Camera error: ${err.message}`)
      }
    }
  }, [stopStream])

  // Start camera on mount
  useEffect(() => {
    startCamera('rear')
    return stopStream          // stop tracks when component unmounts
  }, [startCamera, stopStream])

  // ---- Switch camera -------------------------------------------------------
  const handleSwitch = () => {
    const next = facingMode === 'rear' ? 'front' : 'rear'
    setFacingMode(next)
    startCamera(next)
  }

  // ---- Capture frame -------------------------------------------------------
  const handleCapture = () => {
    const video  = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    canvas.width  = video.videoWidth  || 640
    canvas.height = video.videoHeight || 480
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    setCapturedDataUrl(dataUrl)
    setPhase('captured')
    stopStream()
  }

  // ---- Retake ---------------------------------------------------------------
  const handleRetake = () => {
    setCapturedDataUrl(null)
    startCamera(facingMode)
  }

  // ---- Use photo -----------------------------------------------------------
  const handleUsePhoto = () => {
    if (!capturedDataUrl) return
    // Convert data URL to File
    const byteString = atob(capturedDataUrl.split(',')[1])
    const mime = 'image/jpeg'
    const ab = new ArrayBuffer(byteString.length)
    const ia = new Uint8Array(ab)
    for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i)
    const blob = new Blob([ab], { type: mime })
    const file = new File([blob], `capture-${Date.now()}.jpg`, { type: mime })
    onCapture(file)
  }

  // ---- Close ---------------------------------------------------------------
  const handleClose = () => {
    stopStream()
    onClose()
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div>
      {/* HTTPS / security context warning */}
      {!window.isSecureContext && (
        <div className="alert alert-warning" style={{ marginBottom: '0.75rem' }}>
          ⚠️ <strong>HTTPS required:</strong> Camera access only works on HTTPS or localhost.
        </div>
      )}

      {/* Live viewfinder */}
      {(phase === 'starting' || phase === 'live') && (
        <>
          <video
            ref={videoRef}
            className="camera-video"
            autoPlay
            playsInline
            muted
          />
          {phase === 'starting' && (
            <p className="text-center text-muted mt-1">Starting camera…</p>
          )}
          <div className="camera-controls">
            {phase === 'live' && (
              <button className="btn btn-primary" onClick={handleCapture}>
                📷 Capture
              </button>
            )}
            {canSwitch && phase === 'live' && (
              <button className="btn btn-secondary btn-sm" onClick={handleSwitch}>
                🔄 {facingMode === 'rear' ? 'Front camera' : 'Rear camera'}
              </button>
            )}
            <button className="btn btn-secondary btn-sm" onClick={handleClose}>
              ✕ Close Camera
            </button>
          </div>
        </>
      )}

      {/* Captured preview */}
      {phase === 'captured' && capturedDataUrl && (
        <>
          <div className="preview-container">
            <img src={capturedDataUrl} alt="Captured photo" />
          </div>
          <div className="camera-controls">
            <button className="btn btn-primary" onClick={handleUsePhoto}>
              ✅ Use Photo
            </button>
            <button className="btn btn-secondary" onClick={handleRetake}>
              🔄 Retake
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleClose}>
              ✕ Close Camera
            </button>
          </div>
        </>
      )}

      {/* Error state */}
      {phase === 'error' && (
        <div>
          <div className="alert alert-error">
            <span>📷</span>
            <div>
              <strong>Camera unavailable</strong>
              <p style={{ marginTop: '0.25rem' }}>{errorMsg}</p>
            </div>
          </div>
          <div className="camera-controls">
            <button className="btn btn-secondary" onClick={() => startCamera(facingMode)}>
              🔄 Retry
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleClose}>
              ✕ Close Camera
            </button>
          </div>
        </div>
      )}

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  )
}
