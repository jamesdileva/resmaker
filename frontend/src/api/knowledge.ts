import { apiClient } from './client';
import type {
  KnowledgeItem,
  KnowledgeItemListResponse,
  KnowledgeItemType,
  MatchResult,
} from '../types';

export interface KnowledgeItemFilters {
  skip?: number;
  limit?: number;
  type?: KnowledgeItemType;
  category?: string;
}

export async function listKnowledgeItems(
  filters: KnowledgeItemFilters = {},
): Promise<KnowledgeItemListResponse> {
  const response = await apiClient.get<KnowledgeItemListResponse>(
    '/knowledge-items/',
    { params: filters },
  );
  return response.data;
}

export async function getKnowledgeItem(id: string): Promise<KnowledgeItem> {
  const response = await apiClient.get<KnowledgeItem>(`/knowledge-items/${id}`);
  return response.data;
}

export async function searchKnowledgeItems(
  query: string,
  minScore = 0.3,
): Promise<MatchResult[]> {
  const response = await apiClient.get<MatchResult[]>(
    '/knowledge-items/search',
    { params: { q: query, min_score: minScore } },
  );
  return response.data;
}
