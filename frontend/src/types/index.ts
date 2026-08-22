/**
 * Shared types matching the backend API schemas (Sprint 4).
 */

export type KnowledgeItemType =
  | 'resume_bullet'
  | 'soq_paragraph'
  | 'interview_answer'
  | 'star_story'
  | 'project'
  | 'metric'
  | 'skill';

export interface KnowledgeItem {
  id: string;
  type: KnowledgeItemType;
  title: string | null;
  content: string;
  category: string | null;
  confidence: number | null;
  metadata_json: Record<string, unknown>;
  source_doc_id: string | null;
  created_at: string;
  updated_at: string;
}

export type EvidenceType = 'experience' | 'project' | 'education';

export interface Evidence {
  id: string;
  title: string;
  type: EvidenceType;
  content: string;
  start_date: string | null;
  end_date: string | null;
  company: string | null;
  role: string | null;
  source_doc_id: string | null;
}

export type ApplicationStatus = 'applied' | 'interview' | 'offer' | 'rejected';

export interface Application {
  id: string;
  job_posting_id: string;
  status: ApplicationStatus;
  applied_at: string;
}

export interface KnowledgeItemListResponse {
  items: KnowledgeItem[];
  total: number;
}

export interface MatchResult {
  knowledge_item: KnowledgeItem;
  score: number;
}
