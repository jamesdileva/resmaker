import { useEffect, useRef, useState } from 'react';
import { searchKnowledgeItems } from '../api/knowledge';
import type { MatchResult } from '../types';

const DEFAULT_DEBOUNCE_MS = 300;

interface UseSearchOptions {
  debounceMs?: number;
  minScore?: number;
}

export function useSearch(query: string, options: UseSearchOptions = {}) {
  const { debounceMs = DEFAULT_DEBOUNCE_MS, minScore = 0.3 } = options;
  const [results, setResults] = useState<MatchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const latestQuery = useRef(query);

  useEffect(() => {
    latestQuery.current = query;
    if (query.trim().length === 0) {
      setResults([]);
      setError(null);
      setIsSearching(false);
      return;
    }

    let cancelled = false;
    setIsSearching(true);
    const timer = window.setTimeout(async () => {
      try {
        const found = await searchKnowledgeItems(query.trim(), minScore);
        if (!cancelled && latestQuery.current === query) {
          setResults(found);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setResults([]);
          setError(err instanceof Error ? err.message : 'Search failed');
        }
      } finally {
        if (!cancelled) {
          setIsSearching(false);
        }
      }
    }, debounceMs);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query, debounceMs, minScore]);

  return { results, isSearching, error };
}
