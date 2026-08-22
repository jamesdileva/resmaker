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
