import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { DutyStatementResponse } from './DutyStatementResponse';

const GROUPS = [
  {
    evidence_id: 'ev-1',
    title: 'Duty 1: Resolve customer complaints',
    dates: null,
    bullets: ['Resolved 20+ complaints daily at Boost Mobile'],
  },
  {
    evidence_id: 'ev-2',
    title: 'Duty 2: Maintain confidential records',
    dates: null,
    bullets: ['Maintained organized filing systems'],
  },
];

describe('DutyStatementResponse', () => {
  it('shows an empty hint before parsing', () => {
    render(
      <DutyStatementResponse
        groups={[]}
        excludedIds={[]}
        onToggleExcluded={vi.fn()}
      />,
    );
    expect(screen.getByText(/Parse a duty statement/i)).toBeInTheDocument();
  });

  it('renders each duty with its matched evidence bullet', () => {
    render(
      <DutyStatementResponse
        groups={GROUPS}
        excludedIds={[]}
        onToggleExcluded={vi.fn()}
      />,
    );
    expect(screen.getByText(/Parsed Duties \(2\)/)).toBeInTheDocument();
    expect(screen.getByText('Resolved 20+ complaints daily at Boost Mobile')).toHaveAttribute(
      'data-traceability',
      'ev-1',
    );
  });

  it('toggles exclusion of duty groups', () => {
    const onToggle = vi.fn();
    render(
      <DutyStatementResponse
        groups={GROUPS}
        excludedIds={['ev-2']}
        onToggleExcluded={onToggle}
      />,
    );

    // Excluded group is dimmed but still listed.
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    fireEvent.click(screen.getByLabelText('Toggle Duty 2: Maintain confidential records'));
    expect(onToggle).toHaveBeenCalledWith('ev-2');
  });
});
