/**
 * Types mirroring backend app/models/build.py and app/models/resume.py.
 */

export interface SuggestedItem {
  knowledge_item: {
    id: string;
    type: string;
    title: string | null;
    content: string;
    category: string | null;
  };
  score: number;
  evidence_id: string | null;
}

export interface ExperienceGroup {
  evidence_id: string;
  title: string;
  dates: string | null;
  bullets: string[];
}

export interface RenderedSection {
  title: string;
  section_type: 'profile' | 'experience' | 'skills' | 'projects' | string;
  profile_lines: string[];
  groups: ExperienceGroup[];
  lines: string[];
}

export interface BuiltDocument {
  document_id: string;
  template_name: string;
  sections: RenderedSection[];
  traceability: Record<string, string>;
  warnings: string[];
  metadata?: Record<string, string>;
}
