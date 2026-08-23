import { StarRating } from './StarRating';
import { EvidenceBadge } from './EvidenceBadge';
import type { SearchResponseItem } from '../api/search';

interface ResultsListProps {
  results: SearchResponseItem[];
  isLoading: boolean;
  onSelect?: (itemId: string) => void;
}

export function ResultsList({
  results,
  isLoading,
  onSelect,
}: ResultsListProps) {
  if (isLoading) {
    return (
      <p data-testid="results-loading" style={{ color: 'var(--text-faint)' }}>
        Searching…
      </p>
    );
  }

  if (results.length === 0) {
    return (
      <p data-testid="results-empty" style={{ color: 'var(--text-faint)' }}>
        No matching knowledge items.
      </p>
    );
  }

  return (
    <ul data-testid="results-list" style={{ listStyle: 'none', padding: 0 }}>
      {results.map((result) => (
        <li
          key={result.knowledge_item.id}
          data-testid="result-item"
          onClick={() => onSelect?.(result.knowledge_item.id)}
          style={{
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: 10,
            marginBottom: 10,
            cursor: onSelect ? 'pointer' : 'default',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>
              {result.star_rating > 0 ? (
                <StarRating rating={result.star_rating} />
              ) : (
                <small>browse</small>
              )}{' '}
              <small>{Math.round(result.score * 100)}%</small>
            </span>
            {result.knowledge_item.category && (
              <span
                style={{
                  background: 'var(--chip)',
                  border: '1px solid var(--border)',
                  borderRadius: 999,
                  padding: '1px 8px',
                  fontSize: 12,
                }}
              >
                {result.knowledge_item.category}
              </span>
            )}
          </div>
          <p style={{ margin: '6px 0' }}>
            {result.knowledge_item.content.slice(0, 180)}
            {result.knowledge_item.content.length > 180 ? '…' : ''}
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <small style={{ color: 'var(--text-muted)' }}>
              [{result.knowledge_item.type}]
            </small>
            <EvidenceBadge count={result.evidence_ids.length} />
          </div>
        </li>
      ))}
    </ul>
  );
}
