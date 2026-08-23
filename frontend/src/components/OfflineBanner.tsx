import { useBackendHealth } from '../hooks/useBackendHealth';

export function OfflineBanner() {
  const status = useBackendHealth();

  if (status === 'up') {
    return null;
  }

  return (
    <div
      data-testid="offline-banner"
      role="status"
      style={{
        background: '#7c2d12',
        border: '1px solid #d97706',
        color: '#fde68a',
        padding: '8px 16px',
        fontSize: 14,
      }}
    >
      {status === 'checking'
        ? 'Connecting to the Career OS backend…'
        : 'Backend not reachable on port 8000 — the app starts it automatically '
          + 'when launched from the project; otherwise run scripts/dev.py and wait a moment.'}
    </div>
  );
}
