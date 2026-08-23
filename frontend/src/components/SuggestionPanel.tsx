import { useState } from 'react';
import { suggestEvidence } from '../api/build';
import type { SuggestedItem } from '../types/resume';

/** Star rating thresholds per Implementation Guide section 13.3. */
export function starsForScore(score: number): number {
  if (score >= 0.9) return 5;
  if (score >= 0.8) return 4;
  if (score >= 0.7) return 3;
  if (score >= 0.6) return 2;
  if (score >= 0.5) return 1;
  return 0;
}

interface SuggestionPanelProps {
  selectedIds: string[];
  onAdd: (item: SuggestedItem) => void;
}

export function SuggestionPanel({ selectedIds, onAdd }: SuggestionPanelProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SuggestedItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    if (!query.trim()) {
      return;
    }
    setIsSearching(true);
    setError(null);
    try {
      setResults(await suggestEvidence(query.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div data-testid="suggestion-panel">
      <h3>Find Evidence</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          aria-label="Search query"
          placeholder="Job title or description keywords…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') void runSearch();
          }}
          style={{ flex: 1 }}
        />
        <button onClick={() => void runSearch()} disabled={isSearching}>
          {isSearching ? 'Searching…' : 'Suggest'}
        </button>
      </div>
      {error && (
        <p role="alert" style={{ color: '#dc2626' }}>
          {error}
        </p>
      )}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {results.map((suggestion) => {
          const stars = starsForScore(suggestion.score);
          const alreadySelected = selectedIds.includes(
            suggestion.knowledge_item.id,
          );
          return (
            <li
              key={suggestion.knowledge_item.id}
              data-testid="suggestion-item"
              style={{
                border: '1px solid var(--border)',
                borderRadius: 6,
                padding: 8,
                marginBottom: 8,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span title={`${stars} star match`}>
                  {'★'.repeat(stars)}
                  {'☆'.repeat(5 - stars)}{' '}
                  <small>{Math.round(suggestion.score * 100)}%</small>
                </span>
                <button
                  onClick={() => onAdd(suggestion)}
                  disabled={alreadySelected}
                >
                  {alreadySelected ? 'Added' : 'Add'}
                </button>
              </div>
              <p style={{ margin: '4px 0 0', fontSize: 13 }}>
                {suggestion.knowledge_item.content.slice(0, 120)}
                {suggestion.knowledge_item.content.length > 120 ? '…' : ''}
              </p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
