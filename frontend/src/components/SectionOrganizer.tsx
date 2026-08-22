import { useState } from 'react';
import type { BuiltDocument, RenderedSection } from '../types/resume';

interface SectionOrganizerProps {
  sections: RenderedSection[];
  order: string[];
  onOrderChange: (order: string[]) => void;
}

/** Drag-drop reordering of section keys using native HTML5 events. */
export function SectionOrganizer({
  sections,
  order,
  onOrderChange,
}: SectionOrganizerProps) {
  const [draggingKey, setDraggingKey] = useState<string | null>(null);

  function handleDrop(targetKey: string) {
    if (draggingKey === null || draggingKey === targetKey) {
      return;
    }
    const fromIndex = order.indexOf(draggingKey);
    const toIndex = order.indexOf(targetKey);
    if (fromIndex === -1 || toIndex === -1) {
      return;
    }
    const next = order.filter((key) => key !== draggingKey);
    const adjustedTarget = next.indexOf(targetKey);
    // Moving down inserts after the target; moving up inserts before it.
    const insertAt = fromIndex < toIndex ? adjustedTarget + 1 : adjustedTarget;
    next.splice(insertAt, 0, draggingKey);
    onOrderChange(next);
    setDraggingKey(null);
  }

  return (
    <ul data-testid="section-organizer" style={{ listStyle: 'none', padding: 0 }}>
      {order.map((key) => {
        const section = sections.find((s) => s.section_type === key);
        if (!section) {
          return null;
        }
        return (
          <li
            key={key}
            draggable
            data-testid={`section-handle-${key}`}
            onDragStart={() => setDraggingKey(key)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={() => handleDrop(key)}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              padding: '6px 10px',
              marginBottom: 6,
              cursor: 'grab',
              background: draggingKey === key ? '#eff6ff' : 'transparent',
            }}
          >
            ☰ {section.title}
          </li>
        );
      })}
    </ul>
  );
}

export function orderedSections(
  document: BuiltDocument,
  order: string[],
): RenderedSection[] {
  const byType = new Map(document.sections.map((s) => [s.section_type, s]));
  const ordered = order
    .map((key) => byType.get(key))
    .filter((s): s is RenderedSection => Boolean(s));
  const rest = document.sections.filter(
    (s) => !order.includes(s.section_type),
  );
  return [...ordered, ...rest];
}
