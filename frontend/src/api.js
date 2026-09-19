// Base API URL from environment variable with fallback for local development
const rawBaseUrl = import.meta.env.VITE_API_URL || '';
export const API_BASE = rawBaseUrl.replace(/\/+$/, '');

/**
 * Constructs the full API URL.
 * In production with VITE_API_URL: returns "https://your-backend.com/api/..."
 * In local dev without VITE_API_URL: returns "/api/..." (proxied by Vite)
 */
export function apiUrl(path) {
  if (!path) return API_BASE;
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

export default apiUrl;
