import { useEffect, useState } from 'react';
import {
  checkBackendHealth,
  type BackendHealth,
} from '../api/health';

/**
 * Tracks whether the FastAPI backend on :8000 is reachable. The packaged
 * app spawns its own backend (electron/main.cjs); while uvicorn binds,
 * status flips checking -> up. Re-polls on an interval so a backend that
 * dies later surfaces instead of leaving silent empty views.
 */
export function useBackendHealth(pollMs = 5000): BackendHealth {
  const [status, setStatus] = useState<BackendHealth>('checking');

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      const healthy = await checkBackendHealth();
      if (!cancelled) {
        setStatus(healthy ? 'up' : 'down');
      }
    };

    void check();
    const timer = window.setInterval(check, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [pollMs]);

  return status;
}
