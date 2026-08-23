import axios from 'axios';

// The API client's baseURL points at /api/v1, but /health lives at the
// server root — derive it so this works even when VITE_API_BASE_URL moves.
const ROOT_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1')
  .replace(/\/api\/v1\/?$/, '');

export type BackendHealth = 'checking' | 'up' | 'down';

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${ROOT_URL}/health`, { timeout: 1500 });
    return response.status === 200;
  } catch {
    return false;
  }
}
