// Centralised API base URL — reads from Vite env or falls back to same-origin (proxy)
export const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export const MAX_FILE_MB = 10
export const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
export const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const ALLOWED_EXTS  = ['.jpg', '.jpeg', '.png', '.webp']
