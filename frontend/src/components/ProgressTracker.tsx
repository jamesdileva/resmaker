import type { CSSProperties } from 'react';

export type ProgressPhase =
  | 'idle'
  | 'uploading'
  | 'processing'
  | 'done'
  | 'error';

interface ProgressTrackerProps {
  phase: ProgressPhase;
  progress?: number; // 0..1 for the upload phase
}

const PHASE_LABELS: Record<ProgressPhase, string> = {
  idle: '',
  uploading: 'Uploading…',
  processing: 'Processing document…',
  done: 'Import complete',
  error: 'Import failed',
};

const BAR_COLORS: Record<ProgressPhase, string> = {
  idle: 'transparent',
  uploading: '#2563eb',
  processing: '#d97706',
  done: '#16a34a',
  error: '#dc2626',
};

export function ProgressTracker({ phase, progress = 0 }: ProgressTrackerProps) {
  if (phase === 'idle') {
    return null;
  }

  const indeterminate = phase === 'processing';
  const fraction = indeterminate ? 1 : Math.min(Math.max(progress, 0), 1);

  const barStyle: CSSProperties = indeterminate
    ? {
        background: `repeating-linear-gradient(90deg, ${BAR_COLORS[phase]} 0 12px, transparent 12px 24px)`,
        width: '100%',
      }
    : { background: BAR_COLORS[phase], width: `${fraction * 100}%` };

  return (
    <div data-testid="progress-tracker" style={{ marginTop: 16 }}>
      <p style={{ margin: '0 0 4px', fontWeight: 500 }}>
        {PHASE_LABELS[phase]}
        {!indeterminate && phase === 'uploading' && (
          <> {Math.round(fraction * 100)}%</>
        )}
      </p>
      <div
        style={{
          height: 8,
          borderRadius: 4,
          background: '#e5e7eb',
          overflow: 'hidden',
        }}
      >
        <div
          role="progressbar"
          aria-valuenow={Math.round(fraction * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ ...barStyle, height: '100%', transition: 'width 150ms' }}
        />
      </div>
    </div>
  );
}
