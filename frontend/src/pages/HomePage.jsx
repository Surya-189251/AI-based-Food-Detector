import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { checkHealth, getSupportedFoods } from '../utils/api'

export default function HomePage() {
  const [health, setHealth] = useState(null)
  const [foods,  setFoods]  = useState([])

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => setHealth({ status: 'error', model_ready: false }))
    getSupportedFoods().then(d => setFoods(d.supported_foods || [])).catch(() => {})
  }, [])

  const steps = [
    { icon: '📷', title: 'Capture',  desc: 'Take a photo or upload an image of a supported fruit.' },
    { icon: '🤖', title: 'Analyse',  desc: 'MobileNetV2 classifies the visible freshness.' },
    { icon: '📊', title: 'Results',  desc: 'Get a freshness label, confidence score, and shelf-life estimate.' },
    { icon: '📋', title: 'History',  desc: 'Browse and delete your past analyses anytime.' },
  ]

  return (
    <div className="container" style={{ paddingBottom: '2.5rem' }}>

      {/* Hero */}
      <div style={{ paddingTop: '1.5rem' }}>
        <div className="hero">
          <span className="hero-emoji">🍎</span>
          <h1>FreshCheck AI</h1>
          <p>AI-Based Food Freshness Detection &amp; Shelf-Life Prediction Using Image Processing</p>
          <Link to="/scan" className="btn btn-lg" style={{ background: 'white', color: 'var(--g800)', boxShadow: '0 4px 14px rgba(0,0,0,.18)', fontWeight: 700 }}>
            🔍 Scan Food Now
          </Link>
        </div>
      </div>

      {/* Model status */}
      {health && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.9rem 1.25rem' }}>
          <span className={`status-pill ${health.model_ready ? 'status-pill-ready' : 'status-pill-warning'}`}>
            {health.model_ready ? '● Live' : '● Demo mode'}
          </span>
          <p className="text-small" style={{ color: 'var(--s500)', margin: 0 }}>
            {health.model_ready
              ? 'Model loaded — real predictions active.'
              : 'No trained model found. Scan works but returns "Model not configured." Train the model to enable real predictions.'}
          </p>
        </div>
      )}

      {/* How it works */}
      <div className="card">
        <h2 className="section-title">How It Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.85rem' }}>
          {steps.map(({ icon, title, desc }) => (
            <div key={title} className="step-card">
              <div className="step-icon">{icon}</div>
              <div className="step-title">{title}</div>
              <div className="step-desc">{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Supported foods */}
      <div className="card">
        <h2 className="section-title">Supported Foods</h2>
        {foods.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.85rem' }}>
            {foods.map(f => (
              <span key={f} className="badge badge-fresh" style={{ fontSize: '0.88rem', padding: '0.3rem 1rem' }}>
                {f === 'apple' ? '🍎' : f === 'banana' ? '🍌' : f === 'orange' ? '🍊' : '🍽'}{' '}
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-muted" style={{ marginBottom: '0.75rem' }}>Loading…</p>
        )}
        <p className="text-small" style={{ color: 'var(--s400)', lineHeight: 1.55 }}>
          Supports individual whole fruits on a plain background only.
          <strong> Does not</strong> assess cooked food, meat, dairy, or mixed plates.
        </p>
      </div>

      <div className="safety-notice">
        ⚠️ This tool assesses <em>visible</em> freshness from a photograph only. It cannot detect bacteria,
        toxins, or internal spoilage and <strong>cannot confirm food safety</strong>. Always use your own judgement.
      </div>
    </div>
  )
}
