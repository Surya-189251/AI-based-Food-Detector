import React, { useState, useRef, useCallback } from 'react'
import CameraCapture from '../components/CameraCapture'
import ResultsCard from '../components/ResultsCard'
import { analyzeImage } from '../utils/api'
import { validateImageFile } from '../utils/helpers'

const DEFAULT_OPTS = { storageCondition: 'unknown', wholeOrCut: 'whole', daysSincePurchase: '' }

export default function ScanPage() {
  const fileInputRef = useRef(null)
  const [showCamera, setShowCamera]   = useState(false)
  const [imageFile, setImageFile]     = useState(null)
  const [previewUrl, setPreviewUrl]   = useState(null)
  const [clientError, setClientError] = useState('')
  const [opts, setOpts]               = useState(DEFAULT_OPTS)
  const [loading, setLoading]         = useState(false)
  const [result, setResult]           = useState(null)
  const [serverError, setServerError] = useState('')

  const setImage = useCallback((file) => {
    setClientError(''); setResult(null); setServerError('')
    const err = validateImageFile(file)
    if (err) { setClientError(err); return }
    setImageFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setShowCamera(false)
  }, [])

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setImage(file)
    e.target.value = ''
  }

  const handleAnalyse = async () => {
    if (!imageFile) { setClientError('Please capture or upload an image first.'); return }
    setLoading(true); setServerError(''); setResult(null)
    try {
      setResult(await analyzeImage(imageFile, opts))
    } catch (err) {
      const detail = err?.response?.data?.detail
      setServerError(detail || `Analysis failed (${err?.response?.status ?? 'network error'}). Is the backend running?`)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setImageFile(null); setPreviewUrl(null); setResult(null)
    setClientError(''); setServerError(''); setOpts(DEFAULT_OPTS)
  }

  const handleOptChange = (key) => (e) => setOpts(o => ({ ...o, [key]: e.target.value }))

  return (
    <div className="container" style={{ paddingBottom: '2.5rem' }}>
      <div className="page-header">
        <h1 className="page-title">Scan Food</h1>
        <p className="page-subtitle">Capture or upload a fruit image to check its visible freshness.</p>
      </div>

      {/* Camera view */}
      {showCamera ? (
        <div className="card">
          <CameraCapture
            onCapture={(file) => { setImage(file); setShowCamera(false) }}
            onClose={() => setShowCamera(false)}
          />
        </div>
      ) : (
        <>
          {/* Upload zone — shown when no image yet */}
          {!imageFile && (
            <div className="card">
              {/* Drag-target zone */}
              <div
                className="upload-zone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) setImage(f) }}
              >
                <div className="upload-zone-icon">📂</div>
                <div className="upload-zone-title">Drop an image here or click to browse</div>
                <div className="upload-zone-sub">JPG, PNG, WebP · max 10 MB</div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '1rem 0', color: 'var(--s400)', fontSize: '0.82rem' }}>
                <div style={{ flex: 1, height: 1, background: 'var(--s200)' }} />
                or
                <div style={{ flex: 1, height: 1, background: 'var(--s200)' }} />
              </div>

              <button className="btn btn-primary btn-full btn-lg" onClick={() => setShowCamera(true)}>
                📷 Open Camera
              </button>
              <p className="text-muted text-center" style={{ marginTop: '0.65rem', fontSize: '0.78rem' }}>
                Camera requires HTTPS or localhost
              </p>
              <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style={{ display: 'none' }} onChange={handleFileChange} />
            </div>
          )}

          {/* Preview */}
          {imageFile && !result && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="preview-container">
                <img src={previewUrl} alt="Selected food" />
              </div>
              <div style={{ padding: '0.85rem 1rem', borderTop: '1px solid var(--s100)', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="text-small" style={{ color: 'var(--s400)', flex: 1 }}>{imageFile.name} · {(imageFile.size/1024).toFixed(0)} KB</span>
                <button className="btn btn-secondary btn-sm" onClick={() => { setShowCamera(true) }}>📷 Retake</button>
                <button className="btn btn-secondary btn-sm" onClick={() => fileInputRef.current?.click()}>📂 Replace</button>
                <button className="btn btn-ghost btn-sm" onClick={handleReset} style={{ color: 'var(--r600)' }}>✕</button>
              </div>
              <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style={{ display: 'none' }} onChange={handleFileChange} />
            </div>
          )}
        </>
      )}

      {clientError && <div className="alert alert-error">⚠️ {clientError}</div>}

      {/* Optional context inputs */}
      {imageFile && !result && (
        <div className="card">
          <h3 className="section-title" style={{ marginBottom: '0.85rem' }}>Shelf-life context <span style={{ fontWeight: 400, fontSize: '0.8rem', color: 'var(--s400)' }}>(optional)</span></h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: '0.75rem' }}>
            <div className="form-group mb-0">
              <label className="form-label">Storage</label>
              <select className="form-control" value={opts.storageCondition} onChange={handleOptChange('storageCondition')}>
                <option value="unknown">Unknown</option>
                <option value="room_temp">Room temperature</option>
                <option value="refrigerated">Refrigerated</option>
              </select>
            </div>
            <div className="form-group mb-0">
              <label className="form-label">Condition</label>
              <select className="form-control" value={opts.wholeOrCut} onChange={handleOptChange('wholeOrCut')}>
                <option value="whole">Whole</option>
                <option value="cut">Cut / sliced</option>
              </select>
            </div>
            <div className="form-group mb-0">
              <label className="form-label">Days since purchase</label>
              <input type="number" min="0" max="365" step="0.5" className="form-control" placeholder="e.g. 3" value={opts.daysSincePurchase} onChange={handleOptChange('daysSincePurchase')} />
            </div>
          </div>
        </div>
      )}

      {/* Analyse button */}
      {imageFile && !result && !loading && (
        <button className="btn btn-primary btn-full btn-lg" style={{ marginBottom: '1rem' }} onClick={handleAnalyse}>
          🔍 Analyse Freshness
        </button>
      )}

      {loading && (
        <div className="card text-center">
          <div className="spinner" />
          <p className="text-muted">Analysing image…</p>
        </div>
      )}

      {serverError && <div className="alert alert-error">❌ <strong>Error:</strong> {serverError}</div>}

      {result && (
        <>
          <ResultsCard result={result} imagePreviewUrl={previewUrl} />
          <button className="btn btn-outline btn-full mt-2" onClick={handleReset}>🔄 Analyse another item</button>
        </>
      )}
    </div>
  )
}
