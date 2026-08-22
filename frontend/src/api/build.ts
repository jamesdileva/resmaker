import { apiClient } from './client';
import type { BuiltDocument, SuggestedItem } from '../types/resume';

export async function suggestEvidence(
  query: string,
  options: { minScore?: number; topK?: number } = {},
): Promise<SuggestedItem[]> {
  const response = await apiClient.post<SuggestedItem[]>('/build/suggest', {
    query,
    min_score: options.minScore ?? 0.3,
    top_k: options.topK ?? 10,
  });
  return response.data;
}

export async function buildResume(
  itemIds: string[],
  userProfile: Record<string, unknown> = {},
  template = 'standard',
): Promise<BuiltDocument> {
  const response = await apiClient.post<BuiltDocument>('/build/resume', {
    item_ids: itemIds,
    user_profile: userProfile,
    template,
  });
  return response.data;
}

export interface ExportOptions {
  format: 'docx' | 'txt';
  includeTraceability?: boolean;
}

export interface ValidationIssue {
  rule: string;
  severity: 'error' | 'warning' | string;
  message: string;
  field?: string | null;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  score: number;
}

export type DocType = 'resume' | 'soq' | 'duty';

/**
 * Runs the validation engine over a built document.
 */
export async function validateDocument(
  documentId: string,
  docType: DocType,
  keywords: string[] = [],
): Promise<ValidationResult> {
  const response = await apiClient.post<ValidationResult>('/validate/', {
    document_id: documentId,
    doc_type: docType,
    keywords,
  });
  return response.data;
}

/**
 * Exports a built document and returns the file as a Blob ready for
 * download (the backend streams bytes via /export/download).
 */
export async function exportDocument(
  documentId: string,
  options: ExportOptions,
): Promise<{ blob: Blob; filename: string }> {
  const response = await apiClient.post(
    '/export/download',
    {
      document_id: documentId,
      format: options.format,
      include_traceability: options.includeTraceability ?? true,
      download: true,
    },
    { responseType: 'blob' },
  );

  const disposition: string = response.headers['content-disposition'] ?? '';
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const filename =
    match?.[1] ?? `career-os-export.${options.format}`;
  return { blob: response.data as Blob, filename };
}
