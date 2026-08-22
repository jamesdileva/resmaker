import { apiClient } from './client';
import type { BuiltDocument } from '../types/resume';

export interface DutyRequirement {
  text: string;
  order_index: number;
  category: string;
  keywords: string[];
}

export async function previewDuties(
  rawText: string,
): Promise<DutyRequirement[]> {
  const response = await apiClient.post<{ requirements: DutyRequirement[] }>(
    '/build/duty-preview',
    { raw_text: rawText },
  );
  return response.data.requirements;
}

export async function buildDutyResponse(
  options: {
    rawText?: string;
    jobPostingId?: string;
    selectedItemIds: string[];
  },
): Promise<BuiltDocument> {
  const response = await apiClient.post<BuiltDocument>(
    '/build/duty-statement',
    {
      job_posting_id: options.jobPostingId ?? null,
      raw_text: options.rawText ?? null,
      selected_item_ids: options.selectedItemIds,
    },
  );
  return response.data;
}
