import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { OfflineBanner } from './OfflineBanner';

vi.mock('../api/health', () => ({
  checkBackendHealth: vi.fn(),
}));

import { checkBackendHealth } from '../api/health';

const healthMock = vi.mocked(checkBackendHealth);

describe('OfflineBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the offline notice when the backend is unreachable', async () => {
    healthMock.mockResolvedValue(false);
    render(<OfflineBanner />);
    await waitFor(() =>
      expect(screen.getByTestId('offline-banner').textContent).toContain(
        'Backend not reachable',
      ),
    );
  });

  it('shows a connecting state first, then disappears once healthy', async () => {
    let resolveHealth: (up: boolean) => void = () => {};
    healthMock.mockReturnValue(
      new Promise<boolean>((resolve) => {
        resolveHealth = resolve;
      }),
    );
    const { container } = render(<OfflineBanner />);
    // pending probe -> "connecting" hint is visible
    expect(screen.getByTestId('offline-banner').textContent).toContain(
      'Connecting',
    );
    resolveHealth(true);
    await waitFor(() => expect(container.querySelector('[data-testid="offline-banner"]')).toBeNull());
  });

  it('stays quiet when the backend answers immediately', async () => {
    healthMock.mockResolvedValue(true);
    const { container } = render(<OfflineBanner />);
    await waitFor(() =>
      expect(container.querySelector('[data-testid="offline-banner"]')).toBeNull(),
    );
    expect(healthMock).toHaveBeenCalled();
  });
});
