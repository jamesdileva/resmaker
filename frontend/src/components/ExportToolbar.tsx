import { useState } from 'react';
import { ExportDialog, type ExportFormat } from './ExportDialog';
import { useExport } from '../hooks/useExport';
import { useUI } from '../contexts/UIContext';
import type { DocType } from '../api/build';

interface ExportToolbarProps {
  documentId: string | null;
  defaultFormat?: ExportFormat;
  docType?: DocType;
  keywords?: string[];
}

/** Export controls for a built document; validation errors block export. */
export function ExportToolbar({
  documentId,
  defaultFormat,
  docType,
  keywords,
}: ExportToolbarProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { exportFile, isExporting, lastValidation } = useExport();
  const { toast } = useUI();

  async function handleConfirm(
    format: ExportFormat,
    includeTraceability: boolean,
  ) {
    if (!documentId) {
      return;
    }
    setDialogOpen(false);
    const filename = await exportFile(documentId, {
      format,
      includeTraceability,
      docType,
      keywords,
    });
    if (filename) {
      if (lastValidation && lastValidation.warnings.length > 0) {
        toast(
          `Exported with ${lastValidation.warnings.length} warning(s): ` +
            lastValidation.warnings[0].message,
          'warning',
        );
      } else {
        toast(`Exported ${filename}`, 'success');
      }
    } else {
      toast('Export blocked by validation errors', 'error');
    }
  }

  return (
    <div data-testid="export-toolbar" style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          data-testid="open-export"
          disabled={!documentId || isExporting}
          title={documentId ? undefined : 'Build a document first'}
          onClick={() => setDialogOpen(true)}
        >
          {isExporting ? 'Exporting…' : 'Export'}
        </button>
        <button disabled title="PDF export is planned">
          PDF
        </button>
      </div>
      {lastValidation && !lastValidation.valid && (
        <ul
          data-testid="validation-errors"
          style={{ color: '#dc2626', margin: 0, paddingLeft: 18 }}
        >
          {lastValidation.errors.map((issue, index) => (
            <li key={index}>
              {issue.message}
            </li>
          ))}
        </ul>
      )}
      <ExportDialog
        open={dialogOpen}
        defaultFormat={defaultFormat}
        onConfirm={(format, traceability) =>
          void handleConfirm(format, traceability)
        }
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  );
}
