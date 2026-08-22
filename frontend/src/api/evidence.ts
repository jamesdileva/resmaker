import { apiClient } from './client';
import type { Evidence } from '../types';
import type { KnowledgeItem } from '../types';

export interface EvidenceWithItems {
  evidence: Evidence;
  items: KnowledgeItem[];
}

export async function listEvidence(
  skip = 0,
  limit = 50,
): Promise<Evidence[]> {
  const response = await apiClient.get<Evidence[]>('/evidence/', {
    params: { skip, limit },
  });
  return response.data;
}

export async function getEvidence(id: string): Promise<EvidenceWithItems> {
  const response = await apiClient.get<EvidenceWithItems>(`/evidence/${id}`);
  return response.data;
}
