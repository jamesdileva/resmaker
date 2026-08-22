import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import * as knowledgeApi from '../api/knowledge';
import * as evidenceApi from '../api/evidence';
import type { Evidence, KnowledgeItem, MatchResult } from '../types';

export interface KnowledgeBaseContextType {
  items: KnowledgeItem[];
  evidence: Evidence[];
  isLoading: boolean;
  error: string | null;
  search: (query: string) => Promise<MatchResult[]>;
  getItem: (id: string) => KnowledgeItem | undefined;
  refresh: () => Promise<void>;
}

const KnowledgeBaseContext = createContext<KnowledgeBaseContextType | undefined>(
  undefined,
);

interface ProviderProps {
  children: ReactNode;
}

export function KnowledgeBaseContextProvider({ children }: ProviderProps) {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [itemPage, evidenceList] = await Promise.all([
        knowledgeApi.listKnowledgeItems(),
        evidenceApi.listEvidence(),
      ]);
      setItems(itemPage.items);
      setEvidence(evidenceList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const getItem = useCallback(
    (id: string) => items.find((item) => item.id === id),
    [items],
  );

  const search = useCallback(async (query: string) => {
    return knowledgeApi.searchKnowledgeItems(query);
  }, []);

  const value = useMemo(
    () => ({ items, evidence, isLoading, error, search, getItem, refresh }),
    [items, evidence, isLoading, error, search, getItem, refresh],
  );

  return (
    <KnowledgeBaseContext.Provider value={value}>
      {children}
    </KnowledgeBaseContext.Provider>
  );
}

export function useKnowledgeBase(): KnowledgeBaseContextType {
  const context = useContext(KnowledgeBaseContext);
  if (!context) {
    throw new Error(
      'useKnowledgeBase must be used within KnowledgeBaseContextProvider',
    );
  }
  return context;
}
