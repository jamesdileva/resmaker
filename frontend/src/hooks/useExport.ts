import { useCallback, useState } from 'react';
import { exportDocument, type ExportOptions } from '../api/build';

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function useExport() {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportFile = useCallback(
    async (
      documentId: string,
      options: ExportOptions,
    ): Promise<string | null> => {
      setIsExporting(true);
      setError(null);
      try {
        const { blob, filename } = await exportDocument(documentId, options);
        triggerDownload(blob, filename);
        return filename;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Export failed');
        return null;
      } finally {
        setIsExporting(false);
      }
    },
    [],
  );

  return { exportFile, isExporting, error };
}
