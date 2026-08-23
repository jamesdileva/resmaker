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

export interface SoqBatchRequest {
  questions: string[];
  firstName: string;
  lastName: string;
  positionTitle: string;
  maxWords?: number;
}

export async function buildSoqBatch(
  payload: SoqBatchRequest,
): Promise<BuiltDocument> {
  const response = await apiClient.post<BuiltDocument>('/build/soq-batch', {
    questions: payload.questions,
    first_name: payload.firstName,
    last_name: payload.lastName,
    position_title: payload.positionTitle,
    max_words: payload.maxWords ?? 250,
  });
  return response.data;
}

export interface PastQuestion {
  question: string;
  times_answered: number;
}

export async function getPastQuestions(): Promise<PastQuestion[]> {
  const response = await apiClient.get<PastQuestion[]>('/build/past-questions');
  return response.data;
}

/** Split pasted SOQ text into clean questions (strips numbering, intro
 * boilerplate; keeps only lines that end like questions). */
export function parseSoqQuestions(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*(?:\(?\d+[.)]|[a-z][.)])\s*/i, '').trim())
    .filter((line) => line.endsWith('?'));
}
