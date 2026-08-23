import { GrammarSuggestions } from './GrammarSuggestions';
import { useLLM, type PolishableItem } from '../hooks/useLLM';
import { useUI } from '../contexts/UIContext';
import type { PolishSuggestion } from '../api/llm';

interface PolishPanelProps {
  items: PolishableItem[];
  /** Called with the accepted content updates (item id → new content). */
  onApplyUpdates: (updates: Record<string, string>) => void;
  mode?: 'grammar' | 'transitions';
}

export function PolishPanel({
  items,
  onApplyUpdates,
  mode = 'grammar',
}: PolishPanelProps) {
  const { toast } = useUI();
  const {
    suggestions,
    isPolishing,
    error,
    polish,
    applySuggestion,
    dismissSuggestion,
  } = useLLM();

  const handlePolish = async () => {
    await polish(items, mode);
  };

  const handleAccept = (suggestion: PolishSuggestion) => {
    const updates = applySuggestion(suggestion, items);
    if (Object.keys(updates).length === 0) {
      toast('Suggestion no longer matches the text', 'warning');
      return;
    }
    onApplyUpdates(updates);
    toast('Suggestion applied', 'success');
  };

  return (
    <div data-testid="polish-panel" style={{ marginTop: 12 }}>
      <button
        onClick={handlePolish}
        disabled={isPolishing || items.length === 0}
      >
        {isPolishing ? 'Asking the local model…' : 'Polish with AI'}
      </button>
      {error && (
        <p role="alert" style={{ color: '#dc2626' }}>
          {error}
        </p>
      )}
      <GrammarSuggestions
        suggestions={suggestions}
        onAccept={handleAccept}
        onReject={dismissSuggestion}
      />
    </div>
  );
}
