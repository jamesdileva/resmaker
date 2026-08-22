import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SuggestionPanel, starsForScore } from './SuggestionPanel';

const suggestMock = vi.fn();

vi.mock('../api/build', () => ({
  suggestEvidence: (...args: unknown[]) => suggestMock(...args),
}));

const SUGGESTION = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content: 'Handled confidential records daily',
    category: 'Confidential Information',
  },
  score: 0.85,
  evidence_id: 'ev-1',
};

describe('starsForScore', () => {
  it('maps scores to the documented star thresholds', () => {
    expect(starsForScore(0.95)).toBe(5);
    expect(starsForScore(0.82)).toBe(4);
    expect(starsForScore(0.75)).toBe(3);
    expect(starsForScore(0.65)).toBe(2);
    expect(starsForScore(0.55)).toBe(1);
    expect(starsForScore(0.3)).toBe(0);
  });
});

describe('SuggestionPanel', () => {
  beforeEach(() => {
    suggestMock.mockReset();
  });

  it('searches and renders suggestions with stars and add buttons', async () => {
    suggestMock.mockResolvedValue([SUGGESTION]);
    render(<SuggestionPanel selectedIds={[]} onAdd={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'confidential' },
    });
    fireEvent.click(screen.getByText('Suggest'));

    await waitFor(() => {
      expect(screen.getByTestId('suggestion-item')).toBeInTheDocument();
    });
    expect(screen.getByText(/85%/)).toBeInTheDocument();
    expect(suggestMock).toHaveBeenCalledWith('confidential');
  });

  it('disables Add for already-selected items', async () => {
    suggestMock.mockResolvedValue([SUGGESTION]);
    render(
      <SuggestionPanel selectedIds={['item-1']} onAdd={vi.fn()} />,
    );

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'confidential' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    expect(screen.getByText('Added')).toBeDisabled();
  });

  it('invokes onAdd when a suggestion is added', async () => {
    const onAdd = vi.fn();
    suggestMock.mockResolvedValue([SUGGESTION]);
    render(<SuggestionPanel selectedIds={[]} onAdd={onAdd} />);

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'confidential' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));

    expect(onAdd).toHaveBeenCalledWith(SUGGESTION);
  });

  it('surfaces search errors', async () => {
    suggestMock.mockRejectedValue(new Error('Not found'));
    render(<SuggestionPanel selectedIds={[]} onAdd={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'anything' },
    });
    fireEvent.click(screen.getByText('Suggest'));

    expect(await screen.findByRole('alert')).toHaveTextContent('Not found');
  });
});
