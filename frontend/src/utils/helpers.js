import { ALLOWED_TYPES, ALLOWED_EXTS, MAX_FILE_BYTES, MAX_FILE_MB } from './constants'

/**
 * Client-side image validation.
 * Returns an error string, or null if OK.
 */
export function validateImageFile(file) {
  if (!file) return 'No file selected.'
  if (!ALLOWED_TYPES.includes(file.type)) {
    return `Unsupported format. Please choose a JPG, PNG, or WebP image.`
  }
  if (file.size > MAX_FILE_BYTES) {
    return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${MAX_FILE_MB} MB.`
  }
  if (file.size === 0) return 'File appears to be empty.'
  return null
}

/** Format a UTC ISO timestamp for display */
export function formatDate(isoString) {
  if (!isoString) return '—'
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(isoString))
  } catch {
    return isoString
  }
}

/** Return Tailwind-equivalent CSS class name for a freshness label */
export function freshnessClass(label) {
  if (!label) return 'badge-unknown'
  const l = label.toLowerCase()
  if (l.includes('fresh') && !l.includes('moderate')) return 'badge-fresh'
  if (l.includes('moderate')) return 'badge-moderate'
  if (l.includes('spoil')) return 'badge-spoiled'
  return 'badge-unknown'
}

/** Clamp confidence percentage for display */
export function pct(v) {
  if (v == null) return '—'
  return `${Math.round(v * 100)}%`
}
