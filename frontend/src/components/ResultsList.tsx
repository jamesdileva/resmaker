import { StarRating } from './StarRating';
import type { SearchResponseItem } from '../api/search';

interface ResultsListProps {
  results: SearchResponseItem[];
  isLoading: boolean;
}

export function ResultsList({ results, isLoading }: ResultsListProps) {
  if (isLoading) {
    return (
      <p data-testid="results-loading" style={{ color: '#6b7280' }}>
        Searching…
      </p>
    );
  }

  if (results.length === 0) {
    return (
      <p data-testid="results-empty" style={{ color: '#6b7280' }}>
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
          style={{
            border: '1px solid #e5e7eb',
            borderRadius: 6,
            padding: 10,
            marginBottom: 10,
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
                  background: '#f3f4f6',
                  border: '1px solid #e5e7eb',
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
            <small style={{ color: '#9ca3af' }}>
              [{result.knowledge_item.type}]
            </small>
            <EvidenceBadge evidenceIds={result.evidence_ids} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function EvidenceBadge({ evidenceIds }: { evidenceIds: string[] }) {
  if (evidenceIds.length === 0) {
    return null;
  }
  return (
    <span
      data-testid="evidence-badge"
      title={`Linked to ${evidenceIds.length} evidence record(s)`}
      style={{
        fontSize: 12,
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: 999,
        padding: '1px 8px',
      }}
    >
      ⛓ {evidenceIds.length} evidence
    </span>
  );
}
