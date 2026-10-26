import React from 'react'
import { freshnessClass, pct } from '../utils/helpers'
import { API_BASE } from '../utils/constants'

export default function ResultsCard({ result, imagePreviewUrl }) {
  if (!result) return null

  const {
    model_available, food_type_display, freshness_label, confidence,
    unable_to_assess, is_supported, quality_warnings = [],
    shelf_life, food_safety_notice, model_version, created_at,
    message, image_filename, is_demo,
  } = result

  const imgSrc = imagePreviewUrl || (image_filename ? `${API_BASE}/uploads/${image_filename}` : null)

  return (
    <div>
      {is_demo && (
        <div className="alert alert-info">ℹ️ <strong>Demo — sample output.</strong> Not a real prediction.</div>
      )}

      {/* Image */}
      {imgSrc && (
        <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1rem' }}>
          <div className="preview-container" style={{ maxHeight: 300 }}>
            <img src={imgSrc} alt="Analysed food" />
          </div>
        </div>
      )}

      {/* Quality warnings */}
      {quality_warnings.length > 0 && (
        <div className="alert alert-warning">
          ⚠️ <div>
            <strong>Image quality notice</strong>
            <ul style={{ margin: '0.25rem 0 0 1rem' }}>
              {quality_warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* Model not available */}
      {!model_available && (
        <div className="card" style={{ border: '1px solid #fecaca', background: '#fef2f2' }}>
          <p style={{ fontWeight: 700, color: 'var(--r700)', marginBottom: '0.5rem' }}>🤖 Model not configured</p>
          <p className="text-small" style={{ color: 'var(--s700)', marginBottom: '0.5rem' }}>{message}</p>
          <p className="text-small" style={{ color: 'var(--s500)' }}>
            Train the model first — see <code>docs/DATASET.md</code>.
            Place <code>freshcheck_model.keras</code> + <code>labels.json</code> in <code>backend/saved_models/</code>.
          </p>
        </div>
      )}

      {/* Main result */}
      {model_available && (
        <div className="card">
          {/* Freshness — big visual */}
          <div style={{ textAlign: 'center', padding: '0.5rem 0 1.25rem' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--s400)', marginBottom: '0.5rem' }}>Visible Freshness</div>
            {unable_to_assess || !freshness_label ? (
              <>
                <span className="badge badge-unknown" style={{ fontSize: '1.05rem', padding: '0.45rem 1.5rem' }}>❓ Unable to assess</span>
                {message && <p className="text-small" style={{ color: 'var(--s500)', marginTop: '0.75rem', lineHeight: 1.5 }}>{message}</p>}
              </>
            ) : (
              <span className={`badge ${freshnessClass(freshness_label)}`} style={{ fontSize: '1.05rem', padding: '0.45rem 1.5rem' }}>
                {freshness_label === 'Fresh' ? '✅' : freshness_label === 'Moderately Fresh' ? '🟡' : '🚫'} {freshness_label}
              </span>
            )}
          </div>

          <hr className="divider" />

          {/* Detail rows */}
          <div>
            {food_type_display && (
              <div className="result-row">
                <span className="result-label">Food identified</span>
                <span className="result-value">{food_type_display}</span>
              </div>
            )}
            {!is_supported && (
              <div className="result-row">
                <span className="result-label">Food identified</span>
                <span className="result-value" style={{ color: 'var(--s400)' }}>Unsupported type</span>
              </div>
            )}
            {confidence != null && (
              <div className="result-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.4rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <span className="result-label">Model score</span>
                  <span className="result-value">{pct(confidence)}</span>
                </div>
                <div className="conf-bar-wrap w-full">
                  <div className="conf-bar-fill" style={{ width: `${Math.round(confidence * 100)}%` }} />
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--s400)', lineHeight: 1.4 }}>
                  Raw probability — not a guaranteed reliability measure.
                </p>
              </div>
            )}

            {freshness_label && freshness_label.toLowerCase().includes('spoil') && (
              <div className="alert alert-error" style={{ margin: '0.75rem 0 0' }}>
                🚫 <strong>Suspected spoilage detected.</strong> Do not consume.
              </div>
            )}
          </div>

          <hr className="divider" />

          {/* Shelf life */}
          <div>
            <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.88rem', textTransform: 'uppercase', letterSpacing: '.04em', color: 'var(--s500)' }}>Shelf-life estimate</div>
            {shelf_life?.available ? (
              <>
                <p style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--g800)' }}>
                  {shelf_life.remaining_min}–{shelf_life.remaining_max} day(s) remaining
                </p>
                <p className="text-small" style={{ color: 'var(--s400)', marginTop: '0.2rem' }}>
                  Reference total: {shelf_life.min_days}–{shelf_life.max_days} days · {shelf_life.method}
                </p>
                {shelf_life.assumptions && (
                  <details style={{ marginTop: '0.4rem' }}>
                    <summary className="text-small" style={{ cursor: 'pointer', color: 'var(--g700)', userSelect: 'none' }}>Assumptions & notes</summary>
                    <p className="text-small" style={{ color: 'var(--s500)', marginTop: '0.25rem', lineHeight: 1.5 }}>{shelf_life.assumptions}</p>
                  </details>
                )}
              </>
            ) : (
              <p className="text-small" style={{ color: 'var(--s400)' }}>
                {shelf_life?.message || 'Insufficient information to estimate shelf life.'}
              </p>
            )}
          </div>

          <hr className="divider" />

          <p className="text-muted" style={{ fontSize: '0.75rem' }}>
            Model v{model_version} · {new Date(created_at).toLocaleString()}
          </p>
        </div>
      )}

      <div className="safety-notice">
        ⚠️ {food_safety_notice || 'This tool assesses visible freshness. It cannot detect all harmful bacteria, toxins, or internal spoilage and cannot confirm food safety.'}
      </div>
    </div>
  )
}
