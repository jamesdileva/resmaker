import { useCallback, useMemo, useState } from 'react';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { ContentEditor } from '../components/ContentEditor';
import { DocumentPreview } from '../components/DocumentPreview';
import { ExportToolbar } from '../components/ExportToolbar';
import { SectionOrganizer } from '../components/SectionOrganizer';
import { buildResume } from '../api/build';
import { useBuilder } from '../contexts/BuilderContext';
import { useUI } from '../contexts/UIContext';
import type { BuiltDocument, SuggestedItem } from '../types/resume';

export function ResumeBuilder() {
  const { selectedItems, addSelectedItem, removeSelectedItem, clearSelectedItems } =
    useBuilder();
  const { toast } = useUI();

  const [itemContents, setItemContents] = useState<Record<string, string>>({});
  const [document, setDocument] = useState<BuiltDocument | null>(null);
  const [order, setOrder] = useState<string[]>([
    'profile',
    'experience',
    'skills',
    'projects',
  ]);
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
    if (selectedItems.length === 0) {
      toast('Select at least one evidence item first', 'warning');
      return;
    }
    setIsBuilding(true);
    try {
      const built = await buildResume(selectedItems);
      setDocument(built);
      // Ensure newly built sections appear in the organizer.
      setOrder((current) => [
        ...current,
        ...built.sections
          .map((s) => s.section_type)
          .filter((key) => !current.includes(key)),
      ]);
      if (built.warnings.length > 0) {
        toast(built.warnings[0], 'warning');
      } else {
        toast('Resume built', 'success');
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Build failed', 'error');
    } finally {
      setIsBuilding(false);
    }
  }, [selectedItems, toast]);

  return (
    <div>
      <h2>Resume Builder</h2>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: 320 }}>
          <SuggestionPanel selectedIds={selectedItems} onAdd={handleAdd} />
        </div>
        <div style={{ flex: 1 }}>
          <ContentEditor
            items={selected}
            onRemove={removeSelectedItem}
            onClear={clearSelectedItems}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button onClick={() => void handleBuild()} disabled={isBuilding}>
              {isBuilding ? 'Building…' : 'Build Resume'}
            </button>
            <ExportToolbar documentId={document?.document_id ?? null} />
          </div>
          {document && (
            <div style={{ marginTop: 16 }}>
              <h3>Sections</h3>
              <SectionOrganizer
                sections={document.sections}
                order={order}
                onOrderChange={setOrder}
              />
            </div>
          )}
        </div>
        <div style={{ width: 380 }}>
          <h3>Preview</h3>
          <DocumentPreview document={document} order={order} />
        </div>
      </div>
    </div>
  );
}
