import { apiClient } from './client';
import type { BuiltDocument } from '../types/resume';

export interface SoqAnalysis {
  category: string;
  keywords: string[];
}

export async function analyzeQuestion(question: string): Promise<SoqAnalysis> {
  const response = await apiClient.post<SoqAnalysis>(
    '/build/analyze-question',
    { question },
  );
  return response.data;
}

export async function answerSoq(
  question: string,
  selectedItemIds: string[],
  maxWords = 250,
): Promise<BuiltDocument> {
  const response = await apiClient.post<BuiltDocument>('/build/soq', {
    question,
    selected_item_ids: selectedItemIds,
    max_words: maxWords,
  });
  return response.data;
}

export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}
