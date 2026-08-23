import type { PolishSuggestion } from '../api/llm';

interface GrammarSuggestionsProps {
  suggestions: PolishSuggestion[];
  onAccept: (suggestion: PolishSuggestion) => void;
  onReject: (suggestion: PolishSuggestion) => void;
}

export function GrammarSuggestions({
  suggestions,
  onAccept,
  onReject,
}: GrammarSuggestionsProps) {
  if (suggestions.length === 0) {
    return (
      <p data-testid="polish-empty" style={{ color: 'var(--text-faint)' }}>
        No polish suggestions.
      </p>
    );
  }

  return (
    <ul data-testid="grammar-suggestions" style={{ listStyle: 'none', padding: 0 }}>
      {suggestions.map((suggestion, index) => (
        <li
          key={`${index}-${suggestion.original.slice(0, 24)}`}
          style={{
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: 10,
            marginBottom: 8,
          }}
        >
          <div style={{ marginBottom: 6 }}>
            <del style={{ color: 'var(--text-faint)' }}>{suggestion.original}</del>
            {' → '}
            <span>{suggestion.replacement}</span>
          </div>
          {suggestion.reason && (
            <small style={{ color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
              {suggestion.reason}
            </small>
          )}
          <button onClick={() => onAccept(suggestion)}>Accept</button>{' '}
          <button onClick={() => onReject(suggestion)}>Reject</button>
        </li>
      ))}
    </ul>
  );
}
