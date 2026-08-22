import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressTracker } from './ProgressTracker';

describe('ProgressTracker', () => {
  it('renders nothing when idle', () => {
    const { container } = render(<ProgressTracker phase="idle" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows upload percentage when uploading', () => {
    render(<ProgressTracker phase="uploading" progress={0.5} />);
    expect(screen.getByText(/Uploading/)).toHaveTextContent('50%');
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '50',
    );
  });

  it('shows indeterminate processing state', () => {
    render(<ProgressTracker phase="processing" />);
    expect(screen.getByText(/Processing document/)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '100',
    );
  });

  it('shows done and error states', () => {
    const { rerender } = render(<ProgressTracker phase="done" />);
    expect(screen.getByText('Import complete')).toBeInTheDocument();
    rerender(<ProgressTracker phase="error" />);
    expect(screen.getByText('Import failed')).toBeInTheDocument();
  });
});
