import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { KnowledgeExplorer } from './KnowledgeExplorer';

const searchMock = vi.fn();

vi.mock('../api/search', () => ({
  DEFAULT_FILTERS: {
    itemTypes: [],
    categories: [],
    minStarRating: 0,
    sortBy: 'relevance',
  },
  searchKnowledgeBase: (...args: unknown[]) => searchMock(...args),
}));

const provenanceMock = vi.fn();
vi.mock('../api/knowledge', () => ({
  getKnowledgeProvenance: (...args: unknown[]) => provenanceMock(...args),
}));

const RESULT = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content: 'Handled confidential customer records daily',
    category: 'Confidential Information',
    created_at: '2026-08-22T00:00:00Z',
  },
  score: 0.9,
  star_rating: 5,
  evidence_ids: [],
};

describe('KnowledgeExplorer', () => {
  beforeEach(() => {
    searchMock.mockReset();
    provenanceMock.mockReset();
    provenanceMock.mockResolvedValue({
      knowledge_item: RESULT.knowledge_item,
      source_document: null,
      evidence: [],
      usage: [],
    });
    searchMock.mockResolvedValue({ items: [RESULT], total: 1 });
  });

  it('performs a browse-mode search on mount and shows results', async () => {
    render(<KnowledgeExplorer />);
    await waitFor(() => {
      expect(screen.getByTestId('results-list')).toBeInTheDocument();
    });
    expect(searchMock).toHaveBeenCalledWith('', expect.anything());
    expect(screen.getByText(/1 result/)).toBeInTheDocument();
  });

  it('debounces typed queries into new searches', async () => {
    render(<KnowledgeExplorer />);
    const bar = screen.getByTestId('explorer-search-bar');

    fireEvent.change(bar, { target: { value: 'confidential' } });
    // Chained debounces (input 300ms + page 300ms): assert the eventual
    // behavior rather than exact intermediate call counts.
    await waitFor(
      () => {
        const last = searchMock.mock.calls.at(-1)!;
        expect(last[0]).toBe('confidential');
      },
      { timeout: 3000 },
    );
  });

  it('applies filter changes', async () => {
    render(<KnowledgeExplorer />);

    fireEvent.click(screen.getByLabelText('Resume bullets'));
    await waitFor(() => {
      const lastCall = searchMock.mock.calls.at(-1)!;
      expect(lastCall[1].itemTypes).toEqual(['resume_bullet']);
    });
  });

  it('surfaces API errors as alerts', async () => {
    searchMock.mockRejectedValue(new Error('Request failed'));
    render(<KnowledgeExplorer />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Request failed');
  });

  it('opens the provenance panel when a result is clicked', async () => {
    provenanceMock.mockResolvedValue({
      knowledge_item: RESULT.knowledge_item,
      source_document: null,
      evidence: [],
      usage: [],
    });

    render(<KnowledgeExplorer />);
    await waitFor(() => screen.getAllByTestId('result-item'));

    fireEvent.click(screen.getAllByTestId('result-item')[0]);
    const panel = await screen.findByTestId('provenance-panel');
    expect(panel).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Close provenance panel'));
    await waitFor(() => {
      expect(screen.queryByTestId('provenance-panel')).toBeNull();
    });
  });
});
