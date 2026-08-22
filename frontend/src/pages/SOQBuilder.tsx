import { useCallback, useMemo, useState } from 'react';
import { SOQQuestionInput } from '../components/SOQQuestionInput';
import { SOQEditor } from '../components/SOQEditor';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { DocumentPreview } from '../components/DocumentPreview';
import { ExportToolbar } from '../components/ExportToolbar';
import { answerSoq } from '../api/soq';
import { useBuilder } from '../contexts/BuilderContext';
import { useUI } from '../contexts/UIContext';
import type { BuiltDocument, SuggestedItem } from '../types/resume';

const DEFAULT_MAX_WORDS = 250;

export function SOQBuilder() {
  const { selectedItems, addSelectedItem, removeSelectedItem, clearSelectedItems } =
    useBuilder();
  const { toast } = useUI();

  const [question, setQuestion] = useState('');
  const [maxWords, setMaxWords] = useState(DEFAULT_MAX_WORDS);
  const [itemContents, setItemContents] = useState<Record<string, string>>({});
  const [document, setDocument] = useState<BuiltDocument | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);

  const selected: { id: string; content: string }[] = useMemo(
    () =>
      selectedItems.map((id) => ({
        id,
        content: itemContents[id] ?? '(content unavailable)',
      })),
    [selectedItems, itemContents],
  );

  const handleAdd = useCallback(
    (suggestion: SuggestedItem) => {
      setItemContents((current) => ({
        ...current,
        [suggestion.knowledge_item.id]: suggestion.knowledge_item.content,
      }));
      addSelectedItem(suggestion.knowledge_item.id);
    },
    [addSelectedItem],
  );

  const handleBuild = useCallback(async () => {
    if (question.trim().length < 3) {
      toast('Enter the SOQ question first', 'warning');
      return;
    }
    if (selectedItems.length === 0) {
      toast('Select at least one evidence item', 'warning');
      return;
    }
    setIsBuilding(true);
    try {
      const built = await answerSoq(question.trim(), selectedItems, maxWords);
      setDocument(built);
      if (built.warnings.length > 0) {
        toast(built.warnings[0], 'warning');
      } else {
        toast(
          `SOQ response built (${built.metadata?.['category'] ?? 'General'})`,
          'success',
        );
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Build failed', 'error');
    } finally {
      setIsBuilding(false);
    }
  }, [question, selectedItems, maxWords, toast]);

  return (
    <div>
      <h2>SOQ Builder</h2>
      <SOQQuestionInput value={question} onChange={setQuestion} />

      <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
        <div style={{ width: 300 }}>
          <SuggestionPanel selectedIds={selectedItems} onAdd={handleAdd} />
        </div>
        <div style={{ flex: 1 }}>
          <label>
            Word limit:{' '}
            <input
              type="number"
              aria-label="Word limit"
              min={25}
              max={2000}
              value={maxWords}
              onChange={(event) =>
                setMaxWords(Number(event.target.value) || DEFAULT_MAX_WORDS)
              }
              style={{ width: 80 }}
            />
          </label>
          <SOQEditor
            items={selected}
            maxWords={maxWords}
            onRemove={removeSelectedItem}
            onClear={clearSelectedItems}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button onClick={() => void handleBuild()} disabled={isBuilding}>
              {isBuilding ? 'Building…' : 'Build Response'}
            </button>
            <ExportToolbar documentId={document?.document_id ?? null} docType="soq" />
          </div>
        </div>
        <div style={{ width: 360 }}>
          <h3>Preview</h3>
          <DocumentPreview document={document} order={[]} />
        </div>
      </div>
    </div>
  );
}
