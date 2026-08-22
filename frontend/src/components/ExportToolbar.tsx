import { useState } from 'react';
import { ExportDialog, type ExportFormat } from './ExportDialog';
import { useExport } from '../hooks/useExport';
import { useUI } from '../contexts/UIContext';

interface ExportToolbarProps {
  documentId: string | null;
  defaultFormat?: ExportFormat;
}

/** Export controls for a built document (DOCX/TXT now; PDF stub). */
export function ExportToolbar({ documentId, defaultFormat }: ExportToolbarProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { exportFile, isExporting } = useExport();
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
    });
    if (filename) {
      toast(`Exported ${filename}`, 'success');
    } else {
      toast('Export failed', 'error');
    }
  }

  return (
    <div data-testid="export-toolbar" style={{ display: 'flex', gap: 8 }}>
      <button
        data-testid="open-export"
        disabled={!documentId || isExporting}
        title={
          documentId
            ? undefined
            : 'Build a document first'
        }
        onClick={() => setDialogOpen(true)}
      >
        {isExporting ? 'Exporting…' : 'Export'}
      </button>
      <button disabled title="PDF export is planned">
        PDF
      </button>
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
