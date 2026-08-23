import { useCallback, useEffect, useRef, useState } from 'react';
import { SearchBar } from '../components/SearchBar';
import { SearchFilters } from '../components/SearchFilters';
import { ResultsList } from '../components/ResultsList';
import { ProvenancePanel } from '../components/ProvenancePanel';
import {
  DEFAULT_FILTERS,
  searchKnowledgeBase,
  type SearchFiltersState,
} from '../api/search';
import type { SearchResponseItem } from '../api/search';

const DEBOUNCE_MS = 300;

export function KnowledgeExplorer() {
  const [inputValue, setInputValue] = useState('');
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFiltersState>(DEFAULT_FILTERS);
  const [results, setResults] = useState<SearchResponseItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  const latestRequest = useRef(0);

  const runSearch = useCallback(async () => {
    const requestId = ++latestRequest.current;
    setIsLoading(true);
    setError(null);
    try {
      const response = await searchKnowledgeBase(query, filters);
      if (latestRequest.current === requestId) {
        setResults(response.items);
        setTotal(response.total);
      }
    } catch (err) {
      if (latestRequest.current === requestId) {
        setError(err instanceof Error ? err.message : 'Search failed');
      }
    } finally {
      if (latestRequest.current === requestId) {
        setIsLoading(false);
      }
    }
  }, [query, filters]);

  useEffect(() => {
    const timer = window.setTimeout(() => void runSearch(), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [runSearch]);

  return (
    <div>
      <h2>Evidence Explorer</h2>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: 240 }}>
          <SearchFilters filters={filters} onChange={setFilters} />
        </div>
        <div style={{ flex: 1 }}>
          <SearchBar
            value={inputValue}
            onChange={(value) => {
              setInputValue(value);
              setQuery(value);
            }}
          />
          <p style={{ color: 'var(--text-muted)', margin: '6px 0 12px' }}>
            {isLoading ? '' : `${total} result${total === 1 ? '' : 's'}`}
          </p>
          {error && (
            <p role="alert" style={{ color: '#dc2626' }}>
              {error}
            </p>
          )}
          <ResultsList
            results={results}
            isLoading={isLoading}
            onSelect={setSelectedItemId}
          />
        </div>
      </div>
      {selectedItemId && (
        <ProvenancePanel
          itemId={selectedItemId}
          onClose={() => setSelectedItemId(null)}
        />
      )}
    </div>
  );
}
