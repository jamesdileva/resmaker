import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StarRating } from './StarRating';
import { ResultsList } from './ResultsList';

describe('StarRating', () => {
  it('renders the correct number of filled stars', () => {
    const { rerender } = render(<StarRating rating={4} />);
    expect(screen.getByTestId('star-rating')).toHaveTextContent('★★★★');

    rerender(<StarRating rating={2} />);
    expect(screen.getByTestId('star-rating')).toHaveTextContent('★★☆☆☆');
  });

  it('clamps out-of-range values', () => {
    render(<StarRating rating={9} />);
    expect(screen.getByTestId('star-rating')).toHaveTextContent(
      '★★★★★',
    );
  });
});

const RESULT = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content:
      'Handled confidential customer records daily with discretion and care',
    category: 'Confidential Information',
    created_at: '2026-08-22T00:00:00Z',
  },
  score: 0.92,
  star_rating: 5,
  evidence_ids: ['ev-1'],
};

const UNEVIDENCED = {
  ...RESULT,
  knowledge_item: {
    ...RESULT.knowledge_item,
    id: 'item-2',
    type: 'soq_paragraph',
    category: null as string | null,
  },
  score: 0.3,
  star_rating: 0,
  evidence_ids: [],
};

describe('ResultsList', () => {
  it('shows loading state', () => {
    render(<ResultsList results={[]} isLoading />);
    expect(screen.getByTestId('results-loading')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<ResultsList results={[]} isLoading={false} />);
    expect(screen.getByTestId('results-empty')).toBeInTheDocument();
  });

  it('renders results with stars, score, category, and evidence badge', () => {
    render(<ResultsList results={[RESULT]} isLoading={false} />);

    const item = screen.getAllByTestId('result-item')[0];
    expect(item).toHaveTextContent('92%');
    expect(item).toHaveTextContent('Confidential Information');
    expect(screen.getByTestId('evidence-badge')).toHaveTextContent(
      /1 evidence/,
    );
  });

  it('omits badge and category when absent and marks browse rows', () => {
    render(<ResultsList results={[UNEVIDENCED]} isLoading={false} />);
    expect(screen.queryByTestId('evidence-badge')).toBeNull();
    expect(screen.getByText('browse')).toBeInTheDocument();
  });
});
