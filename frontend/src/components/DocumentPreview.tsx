import { orderedSections } from './SectionOrganizer';
import type { BuiltDocument } from '../types/resume';

interface DocumentPreviewProps {
  document: BuiltDocument | null;
  order: string[];
}

export function DocumentPreview({ document, order }: DocumentPreviewProps) {
  if (!document) {
    return (
      <div data-testid="document-preview-empty" style={{ color: 'var(--text-faint)' }}>
        Build a resume to see the preview.
      </div>
    );
  }

  return (
    <div data-testid="document-preview">
      <small style={{ color: 'var(--text-muted)' }}>
        {document.document_id.slice(0, 8)} · template: {document.template_name}
      </small>
      {orderedSections(document, order).map((section, sectionIndex) => (
        <section
          key={`${section.section_type}-${sectionIndex}`}
          style={{ marginTop: 16 }}
        >
          <h3 style={{ margin: '0 0 6px', textTransform: 'uppercase' }}>
            {section.title}
          </h3>
          {section.profile_lines.length > 0 && (
            <div>
              {section.profile_lines.map((line, index) => (
                <p key={index} style={{ margin: '2px 0' }}>
                  {line}
                </p>
              ))}
            </div>
          )}
          {section.groups.map((group) => (
            <div key={group.evidence_id} style={{ marginBottom: 10 }}>
              <strong>{group.title}</strong>
              {group.dates && (
                <span style={{ color: 'var(--text-faint)' }}> ({group.dates})</span>
              )}
              <ul style={{ margin: '4px 0 0' }}>
                {group.bullets.map((bullet, index) => (
                  <li key={index} data-traceability={group.evidence_id}>
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {section.lines.map((line, index) => (
            <p key={index} style={{ margin: '2px 0' }}>
              • {line}
            </p>
          ))}
        </section>
      ))}
    </div>
  );
}
