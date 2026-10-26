import axios from 'axios'
import { API_BASE } from './constants'

const api = axios.create({ baseURL: API_BASE })

export async function checkHealth() {
  const { data } = await api.get('/api/health')
  return data
}

export async function getSupportedFoods() {
  const { data } = await api.get('/api/foods')
  return data
}

/**
 * Analyse an image file.
 * @param {File} file
 * @param {object} opts  { storageCondition, wholeOrCut, daysSincePurchase }
 */
export async function analyzeImage(file, opts = {}) {
  const form = new FormData()
  form.append('image', file)
  form.append('storage_condition', opts.storageCondition || 'unknown')
  form.append('whole_or_cut',      opts.wholeOrCut      || 'whole')
  if (opts.daysSincePurchase != null && opts.daysSincePurchase !== '') {
    form.append('days_since_purchase', String(opts.daysSincePurchase))
  }
  const { data } = await api.post('/api/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getHistory(limit = 50, offset = 0) {
  const { data } = await api.get('/api/history', { params: { limit, offset } })
  return data
}

export async function deleteRecord(id) {
  const { data } = await api.delete(`/api/history/${id}`)
  return data
}

export async function clearHistory() {
  const { data } = await api.delete('/api/history')
  return data
}
