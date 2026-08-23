import { useCallback, useState } from 'react';
import {
  polishText,
  type PolishSuggestion,
} from '../api/llm';

export interface PolishableItem {
  id: string;
  content: string;
}

export function useLLM() {
  const [suggestions, setSuggestions] = useState<PolishSuggestion[]>([]);
  const [isPolishing, setIsPolishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const polish = useCallback(
    async (items: PolishableItem[], mode: 'grammar' | 'transitions' = 'grammar') => {
      if (items.length === 0) return;
      setIsPolishing(true);
      setError(null);
      try {
        const combined = items.map((item) => item.content).join('\n');
        setSuggestions(await polishText(combined, mode));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Polish failed');
        setSuggestions([]);
      } finally {
        setIsPolishing(false);
      }
    },
    [],
  );

  /** Accept a suggestion: rewrite the owning item's content in place. */
  const applySuggestion = useCallback(
    (
      suggestion: PolishSuggestion,
      items: PolishableItem[],
    ): Record<string, string> => {
      const updates: Record<string, string> = {};
      for (const item of items) {
        if (item.content.includes(suggestion.original)) {
          updates[item.id] = item.content.replace(
            suggestion.original,
            suggestion.replacement,
          );
          break;
        }
      }
      setSuggestions((current) => current.filter((s) => s !== suggestion));
      return updates;
    },

    [],
  );

  const dismissSuggestion = useCallback((suggestion: PolishSuggestion) => {
    setSuggestions((current) => current.filter((s) => s !== suggestion));
  }, []);

  const reset = useCallback(() => {
    setSuggestions([]);
    setError(null);
  }, []);

  return {
    suggestions,
    isPolishing,
    error,
    polish,
    applySuggestion,
    dismissSuggestion,
    reset,
  };
}
