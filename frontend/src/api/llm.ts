import { apiClient } from './client';

export interface PolishSuggestion {
  original: string;
  replacement: string;
  type: string;
  reason: string;
}

export interface LLMConfig {
  enabled: boolean;
  endpoint: string;
  model: string;
  max_tokens: number;
  temperature: number;
}

export async function getLlmConfig(): Promise<LLMConfig> {
  const response = await apiClient.get<LLMConfig>('/llm/config');
  return response.data;
}

export async function updateLlmConfig(config: LLMConfig): Promise<LLMConfig> {
  const response = await apiClient.put<LLMConfig>('/llm/config', config);
  return response.data;
}

export async function polishText(
  text: string,
  mode: 'grammar' | 'transitions',
): Promise<PolishSuggestion[]> {
  const path = mode === 'transitions' ? '/llm/transitions' : '/llm/grammar';
  const response = await apiClient.post<PolishSuggestion[]>(path, { text });
  return response.data;
}

export async function expandKeywords(query: string, limit = 8): Promise<string[]> {
  const response = await apiClient.post<string[]>('/llm/keywords', {
    query,
    limit,
  });
  return response.data;
}
