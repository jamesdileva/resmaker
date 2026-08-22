import { useCallback, useState } from 'react';
import {
  exportDocument,
  validateDocument,
  type DocType,
  type ExportOptions,
  type ValidationResult,
} from '../api/build';

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

export interface ExportRequestOptions extends ExportOptions {
  docType?: DocType;
  keywords?: string[];
}

/**
 * Validates before exporting: errors block the download and are
 * reported via `blockedBy`; warnings pass through as non-blocking.
 */
export function useExport() {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastValidation, setLastValidation] = useState<ValidationResult | null>(
    null,
  );

  const exportFile = useCallback(
    async (
      documentId: string,
      options: ExportRequestOptions,
    ): Promise<string | null> => {
      setIsExporting(true);
      setError(null);
      setLastValidation(null);
      try {
        let validation: ValidationResult | null = null;
        if (options.docType) {
          validation = await validateDocument(
            documentId,
            options.docType,
            options.keywords ?? [],
          );
          setLastValidation(validation);

          if (!validation.valid) {
            setError(
              `Export blocked: ${validation.errors.length} validation error(s)`,
            );
            return null;
          }
        }

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

  return { exportFile, isExporting, error, lastValidation };
}
