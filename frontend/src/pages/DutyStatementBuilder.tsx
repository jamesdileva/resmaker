import { useCallback, useMemo, useState } from 'react';
import { DutyStatementInput } from '../components/DutyStatementInput';
import { DutyStatementResponse } from '../components/DutyStatementResponse';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { DocumentPreview } from '../components/DocumentPreview';
import { previewDuties } from '../api/duty';
import type { DutyRequirement } from '../api/duty';
import { buildDutyResponse } from '../api/duty';
import { useBuilder } from '../contexts/BuilderContext';
import { useUI } from '../contexts/UIContext';
import type { BuiltDocument, SuggestedItem } from '../types/resume';

export function DutyStatementBuilder() {
  const { selectedItems, addSelectedItem, removeSelectedItem, clearSelectedItems } =
    useBuilder();
  const { toast } = useUI();

  const [duties, setDuties] = useState<DutyRequirement[]>([]);
  const [rawText, setRawText] = useState('');
  const [excludedIds, setExcludedIds] = useState<string[]>([]);
  const [itemContents, setItemContents] = useState<Record<string, string>>({});
  const [document, setDocument] = useState<BuiltDocument | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);

  // The response groups are keyed by evidence_id; excludedIds tracks which
  // duty groups the user has toggled out of the final view.
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

  const handleParse = useCallback(
    async (text: string) => {
      setIsParsing(true);
      try {
        const parsed = await previewDuties(text.trim());
        if (parsed.length === 0) {
          toast('No duties could be parsed from that text', 'warning');
        }
        setDuties(parsed);
        setRawText(text.trim());
        setExcludedIds([]);
        setDocument(null);
      } catch (err) {
        toast(err instanceof Error ? err.message : 'Parse failed', 'error');
      } finally {
        setIsParsing(false);
      }
    },
    [toast],
  );

  const handleBuild = useCallback(async () => {
    if (duties.length === 0 || !rawText) {
      toast('Parse a duty statement first', 'warning');
      return;
    }
    if (selectedItems.length === 0) {
      toast('Select at least one evidence item', 'warning');
      return;
    }
    setIsBuilding(true);
    try {
      const built = await buildDutyResponse({
        rawText,
        selectedItemIds: selectedItems,
      });
      setDocument(built);
      if (built.warnings.length > 0) {
        toast(built.warnings[0], 'warning');
      } else {
        toast('Duty statement response built', 'success');
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Build failed', 'error');
    } finally {
      setIsBuilding(false);
    }
  }, [duties.length, rawText, selectedItems, toast]);

  return (
    <div>
      <h2>Duty Statement Builder</h2>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: 340 }}>
          <DutyStatementInput
            onParse={(text) => void handleParse(text)}
            disabled={isParsing}
          />
          <div style={{ marginTop: 16 }}>
            <SuggestionPanel selectedIds={selectedItems} onAdd={handleAdd} />
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <ContentEditorSummary
            count={selectedItems.length}
            items={selected}
            onRemove={removeSelectedItem}
            onClear={clearSelectedItems}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button onClick={() => void handleBuild()} disabled={isBuilding}>
              {isBuilding ? 'Building…' : 'Build Response'}
            </button>
            <button
              disabled
              title="Export arrives with the export pipeline"
            >
              Export
            </button>
          </div>
          {document && (
            <div style={{ marginTop: 16 }}>
              <h3>Assembled Response</h3>
              <DocumentPreview document={document} order={['duty_response']} />
            </div>
          )}
        </div>
        <div style={{ width: 360 }}>
          <DutyStatementResponse
            groups={
              document?.sections.find((s) => s.section_type === 'duty_response')
                ?.groups ?? []
            }
            excludedIds={excludedIds}
            onToggleExcluded={(id) =>
              setExcludedIds((current) =>
                current.includes(id)
                  ? current.filter((key) => key !== id)
                  : [...current, id],
              )
            }
          />
        </div>
      </div>
    </div>
  );
}

interface ContentEditorSummaryProps {
  count: number;
  items: { id: string; content: string }[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

function ContentEditorSummary({
  count,
  items,
  onRemove,
  onClear,
}: ContentEditorSummaryProps) {
  return (
    <div data-testid="content-editor">
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h3>Selected Evidence ({count})</h3>
        {count > 0 && (
          <button aria-label="Clear selection" onClick={onClear}>
            Clear all
          </button>
        )}
      </div>
      {count === 0 ? (
        <p style={{ color: '#6b7280' }}>
          Add evidence suggestions to support your duty responses.
        </p>
      ) : (
        <ol>
          {items.map((item) => (
            <li key={item.id}>
              {item.content.slice(0, 80)}
              {item.content.length > 80 ? '…' : ''}{' '}
              <button aria-label={`Remove item ${item.id}`} onClick={() => onRemove(item.id)}>
                ✕
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
