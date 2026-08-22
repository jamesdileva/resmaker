import { apiClient } from './client';
import type {
  KnowledgeItem,
  KnowledgeItemListResponse,
  KnowledgeItemType,
} from '../types';
import type { MatchResult } from '../types';

export interface ProvenanceData {
  knowledge_item: KnowledgeItem;
  source_document: {
    id: string;
    filename: string;
    file_type: string;
    imported_at: string;
  } | null;
  evidence: {
    id: string;
    title: string;
    type: string;
    company: string | null;
    role: string | null;
    strength: number;
    success_rate: number;
  }[];
  usage: {
    application_id: string;
    applied_at: string;
    application_status: string;
    result: string | null;
    used_in_resume: boolean;
    used_in_soq: boolean;
    used_in_duty: boolean;
  }[];
}

export async function getKnowledgeProvenance(
  id: string,
): Promise<ProvenanceData> {
  const response = await apiClient.get<ProvenanceData>(
    `/knowledge-items/${id}/provenance`,
  );
  return response.data;
}

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
