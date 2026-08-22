import { useCallback, useEffect, useState } from 'react';
import { listKnowledgeItems } from '../api/knowledge';
import type { KnowledgeItemFilters } from '../api/knowledge';
import type { KnowledgeItem } from '../types';

export function useKnowledgeItems(filters: KnowledgeItemFilters = {}) {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listKnowledgeItems(filters);
      setItems(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load items');
    } finally {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    void fetchItems();
  }, [fetchItems]);

  return { items, total, isLoading, error, refetch: fetchItems };
}
