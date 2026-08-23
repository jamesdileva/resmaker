interface SelectedItem {
  id: string;
  content: string;
}

interface ContentEditorProps {
  items: SelectedItem[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

export function ContentEditor({ items, onRemove, onClear }: ContentEditorProps) {
  return (
    <div data-testid="content-editor">
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h3>Selected Evidence ({items.length})</h3>
        {items.length > 0 && (
          <button onClick={onClear} aria-label="Clear selection">
            Clear all
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <p style={{ color: 'var(--text-faint)' }}>
          Add evidence from the suggestions panel to build your resume.
        </p>
      ) : (
        <ol>
          {items.map((item) => (
            <li key={item.id}>
              {item.content.slice(0, 100)}
              {item.content.length > 100 ? '…' : ''}{' '}
              <button
                aria-label={`Remove item ${item.id}`}
                onClick={() => onRemove(item.id)}
              >
                ✕
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
