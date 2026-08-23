import { useMemo } from 'react';
import { countWords } from '../api/soq';

interface SelectedItem {
  id: string;
  content: string;
}

interface SOQEditorProps {
  items: SelectedItem[];
  maxWords?: number;
  onRemove: (id: string) => void;
  onClear: () => void;
}

export function SOQEditor({
  items,
  maxWords = 250,
  onRemove,
  onClear,
}: SOQEditorProps) {
  const wordCount = useMemo(
    () => items.reduce((total, item) => total + countWords(item.content), 0),
    [items],
  );
  const fraction = Math.min(wordCount / maxWords, 1);
  const overLimit = wordCount > maxWords;
  const barColor = overLimit ? '#dc2626' : fraction > 0.8 ? '#d97706' : '#16a34a';

  return (
    <div data-testid="soq-editor">
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h3>Response Evidence ({items.length})</h3>
        {items.length > 0 && (
          <button onClick={onClear} aria-label="Clear evidence selection">
            Clear all
          </button>
        )}
      </div>

      <p
        data-testid="word-count"
        style={{
          margin: '0 0 4px',
          color: overLimit ? '#dc2626' : undefined,
          fontWeight: overLimit ? 600 : undefined,
        }}
      >
        {wordCount} / {maxWords} words
        {overLimit ? ' — over limit' : ''}
      </p>
      <div
        style={{
          height: 6,
          borderRadius: 3,
          background: 'var(--chip)',
          overflow: 'hidden',
        }}
      >
        <div
          role="progressbar"
          aria-valuenow={Math.round(fraction * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ width: `${fraction * 100}%`, height: '100%', background: barColor }}
        />
      </div>

      {items.length === 0 ? (
        <p style={{ color: 'var(--text-faint)' }}>
          Add evidence suggestions to compose your response.
        </p>
      ) : (
        <ol>
          {items.map((item) => (
            <li key={item.id} data-evidence-marker={item.id}>
              {item.content.slice(0, 120)}
              {item.content.length > 120 ? '…' : ''}{' '}
              <button aria-label={`Remove ${item.id}`} onClick={() => onRemove(item.id)}>
                ✕
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
