import { useState } from 'react';

export type ExportFormat = 'docx' | 'txt';

interface ExportDialogProps {
  open: boolean;
  defaultFormat?: ExportFormat;
  onConfirm: (format: ExportFormat, includeTraceability: boolean) => void;
  onCancel: () => void;
}

/** Format selection + traceability toggle for exporting a built doc. */
export function ExportDialog({
  open,
  defaultFormat = 'docx',
  onConfirm,
  onCancel,
}: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>(defaultFormat);
  const [includeTraceability, setIncludeTraceability] = useState(true);

  if (!open) {
    return null;
  }

  return (
    <div
      data-testid="export-dialog"
      role="dialog"
      aria-label="Export document"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.35)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 8,
          padding: 20,
          minWidth: 300,
        }}
      >
        <h3 style={{ marginTop: 0 }}>Export Document</h3>

        <fieldset style={{ border: 'none', padding: 0 }}>
          <legend>
            <strong>Format</strong>
          </legend>
          <label style={{ display: 'block' }}>
            <input
              type="radio"
              name="export-format"
              checked={format === 'docx'}
              onChange={() => setFormat('docx')}
            />{' '}
            DOCX (Word)
          </label>
          <label style={{ display: 'block' }}>
            <input
              type="radio"
              name="export-format"
              checked={format === 'txt'}
              onChange={() => setFormat('txt')}
            />{' '}
            TXT (plain text)
          </label>
          <label style={{ display: 'block', color: '#9ca3af' }}>
            <input type="radio" disabled /> PDF (coming soon)
          </label>
        </fieldset>

        <label style={{ display: 'block', marginTop: 12 }}>
          <input
            data-testid="traceability-toggle"
            type="checkbox"
            checked={includeTraceability}
            onChange={(event) => setIncludeTraceability(event.target.checked)}
          />{' '}
          Include traceability report
        </label>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 8,
            marginTop: 16,
          }}
        >
          <button onClick={onCancel}>Cancel</button>
          <button
            data-testid="confirm-export"
            onClick={() => onConfirm(format, includeTraceability)}
          >
            Export
          </button>
        </div>
      </div>
    </div>
  );
}
