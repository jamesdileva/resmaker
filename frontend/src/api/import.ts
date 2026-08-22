import { apiClient } from './client';

export interface ImportJobResult {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  source_doc_id?: string | null;
  items_created?: number;
  items_skipped?: number;
  error?: string | null;
}

export const SUPPORTED_IMPORT_TYPES = ['docx', 'pdf', 'txt'] as const;

export function getFileExtension(filename: string): string {
  if (!filename.includes('.')) {
    return '';
  }
  return filename.split('.').pop()?.toLowerCase() ?? '';
}

export async function uploadDocument(
  file: File,
  options: {
    onUploadProgress?: (fraction: number) => void;
    fileType?: string;
  } = {},
): Promise<ImportJobResult> {
  const form = new FormData();
  form.append('file', file);
  if (options.fileType) {
    form.append('file_type', options.fileType);
  }

  const response = await apiClient.post<ImportJobResult>('/import/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (event.total) {
        options.onUploadProgress?.(event.loaded / event.total);
      }
    },
  });
  return response.data;
}

export async function getImportStatus(jobId: string): Promise<ImportJobResult> {
  const response = await apiClient.get<ImportJobResult>(
    `/import/status/${jobId}`,
  );
  return response.data;
}

/**
 * Polls an import job until it completes or fails.
 * Returns the final status record.
 */
export async function pollImportStatus(
  jobId: string,
  { maxAttempts = 10, intervalMs = 500 } = {},
): Promise<ImportJobResult> {
  let last: ImportJobResult | undefined;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    last = await getImportStatus(jobId);
    if (last.status !== 'processing') {
      return last;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return last ?? { job_id: jobId, status: 'failed', error: 'Polling timed out' };
}
