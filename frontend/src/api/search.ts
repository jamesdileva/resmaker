import { apiClient } from './client';

export interface SearchFiltersState {
  itemTypes: string[];
  categories: string[];
  minStarRating: number;
  sortBy: 'relevance' | 'date';
}

export const DEFAULT_FILTERS: SearchFiltersState = {
  itemTypes: [],
  categories: [],
  minStarRating: 0,
  sortBy: 'relevance',
};

export interface SearchResponseItem {
  knowledge_item: {
    id: string;
    type: string;
    title: string | null;
    content: string;
    category: string | null;
    created_at: string;
  };
  score: number;
  star_rating: number;
  evidence_ids: string[];
}

export interface SearchResponse {
  items: SearchResponseItem[];
  total: number;
}

export async function searchKnowledgeBase(
  query: string,
  filters: SearchFiltersState,
  limit = 50,
): Promise<SearchResponse> {
  const response = await apiClient.post<SearchResponse>('/search/', {
    query,
    item_types: filters.itemTypes,
    categories: filters.categories,
    min_star_rating: filters.minStarRating,
    sort_by: filters.sortBy,
    limit,
  });
  return response.data;
}
