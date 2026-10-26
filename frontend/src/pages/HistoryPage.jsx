import React, { useEffect, useState, useCallback } from 'react'
import { getHistory, deleteRecord, clearHistory } from '../utils/api'
import { formatDate, freshnessClass, pct } from '../utils/helpers'
import { API_BASE } from '../utils/constants'

export default function HistoryPage() {
  const [records, setRecords]       = useState([])
  const [total,   setTotal]         = useState(0)
  const [loading, setLoading]       = useState(true)
  const [error,   setError]         = useState('')
  const [confirmClear, setConfirmClear] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await getHistory(50, 0)
      setRecords(data.records || [])
      setTotal(data.total || 0)
    } catch { setError('Could not load history. Is the backend running?') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    try {
      await deleteRecord(id)
      setRecords(r => r.filter(x => x.id !== id))
      setTotal(t => t - 1)
    } catch { alert('Failed to delete record.') }
  }

  const handleClearAll = async () => {
    try {
      await clearHistory()
      setRecords([]); setTotal(0); setConfirmClear(false)
    } catch { alert('Failed to clear history.') }
  }

  return (
    <div className="container" style={{ paddingBottom: '2.5rem' }}>
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h1 className="page-title">History</h1>
            <p className="page-subtitle">{total} record{total !== 1 ? 's' : ''} stored.</p>
          </div>
          {records.length > 0 && !confirmClear && (
            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--r600)', borderColor: 'var(--r400)' }} onClick={() => setConfirmClear(true)}>
              🗑 Clear all
            </button>
          )}
        </div>
      </div>

      {confirmClear && (
        <div className="alert alert-error">
          <div>
            <strong>Delete all {total} record(s)?</strong> This also removes uploaded images.
            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-danger btn-sm" onClick={handleClearAll}>Yes, delete all</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setConfirmClear(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="spinner" />}

      {!loading && records.length === 0 && !error && (
        <div className="card text-center" style={{ padding: '3rem 1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>📋</div>
          <p style={{ fontWeight: 600, color: 'var(--s700)', marginBottom: '0.25rem' }}>No history yet</p>
          <p className="text-muted">Scan a fruit to get started.</p>
        </div>
      )}

      {!loading && records.map(r => <HistoryRow key={r.id} record={r} onDelete={handleDelete} />)}

      {records.length > 0 && (
        <div className="safety-notice" style={{ marginTop: '0.5rem' }}>
          📁 Records and images are stored in <code>backend/data/</code>. Deleting a record removes its image file.
        </div>
      )}
    </div>
  )
}

function HistoryRow({ record, onDelete }) {
  const [expanded,   setExpanded]   = useState(false)
  const [confirmDel, setConfirmDel] = useState(false)

  const imgSrc = record.image_filename ? `${API_BASE}/uploads/${record.image_filename}` : null
  const foodName = record.food_type ? record.food_type.charAt(0).toUpperCase() + record.food_type.slice(1) : 'Unknown'
  const emoji = record.food_type === 'apple' ? '🍎' : record.food_type === 'banana' ? '🍌' : record.food_type === 'orange' ? '🍊' : '🍽'

  return (
    <div className="history-item">
      <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
        {/* Thumbnail */}
        {imgSrc ? (
          <img src={imgSrc} alt="food" style={{ width: 64, height: 64, objectFit: 'cover', borderRadius: '10px', flexShrink: 0, background: 'var(--s100)' }}
            onError={e => { e.target.style.display = 'none' }} />
        ) : (
          <div style={{ width: 64, height: 64, background: 'var(--s100)', borderRadius: '10px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.75rem' }}>{emoji}</div>
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', alignItems: 'center', marginBottom: '0.2rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.97rem' }}>{emoji} {foodName}</span>
            {record.freshness_label
              ? <span className={`badge ${freshnessClass(record.freshness_label)}`} style={{ fontSize: '0.76rem' }}>{record.freshness_label}</span>
              : <span className="badge badge-unknown" style={{ fontSize: '0.76rem' }}>Unable to assess</span>}
          </div>
          <p className="text-muted" style={{ fontSize: '0.78rem' }}>{formatDate(record.created_at)}{record.confidence != null ? ` · ${pct(record.confidence)}` : ''}</p>
        </div>

        <div style={{ display: 'flex', gap: '0.3rem', flexShrink: 0 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setExpanded(e => !e)}>
            {expanded ? '▲' : '▼'}
          </button>
          {!confirmDel
            ? <button className="btn btn-ghost btn-sm" style={{ color: 'var(--r600)' }} onClick={() => setConfirmDel(true)}>🗑</button>
            : <>
                <button className="btn btn-danger btn-sm" onClick={() => onDelete(record.id)}>Delete</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setConfirmDel(false)}>Cancel</button>
              </>
          }
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--s100)', fontSize: '0.85rem', color: 'var(--s700)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.3rem 1rem' }}>
          {record.shelf_life_estimate && <p><span style={{ color: 'var(--s400)' }}>Shelf life</span><br />{record.shelf_life_estimate}</p>}
          {record.storage_condition   && <p><span style={{ color: 'var(--s400)' }}>Storage</span><br />{record.storage_condition}</p>}
          {record.whole_or_cut        && <p><span style={{ color: 'var(--s400)' }}>Condition</span><br />{record.whole_or_cut}</p>}
          {record.model_version       && <p><span style={{ color: 'var(--s400)' }}>Model</span><br />v{record.model_version}</p>}
          {record.quality_warning     && <p style={{ gridColumn: '1/-1' }}><span style={{ color: 'var(--s400)' }}>⚠️ Quality</span><br />{record.quality_warning}</p>}
        </div>
      )}
    </div>
  )
}
