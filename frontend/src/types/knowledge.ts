export interface CandidateExperience {
  title: string;
  company: string;
  duration?: string;
  highlights?: string[];
}

export interface CandidateProject {
  name: string;
  description: string;
  technologies?: string[];
  url?: string;
}

export interface CandidateEducation {
  degree: string;
  institution: string;
  year?: string;
}

export interface CandidateProfile {
  id: number;
  user_id: number;
  full_name: string | null;
  headline: string | null;
  summary: string | null;
  skills: string[];
  experience: CandidateExperience[];
  projects: CandidateProject[];
  education: CandidateEducation[];
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateProfileUpdate {
  headline?: string;
  summary?: string;
  skills?: string[];
  experience?: CandidateExperience[];
  projects?: CandidateProject[];
  education?: CandidateEducation[];
}

export interface KnowledgeSyncResponse {
  message: string;
  synced_items_count: number;
  skipped_items_count: number;
  total_chunks: number;
  last_synced_at: string;
  profile_updated: boolean;
}

export interface RetrievedChunkItem {
  chunk_id: string;
  content: string;
  score: number;
  source_type: string;
  title: string;
  url: string | null;
  chunk_index: number;
  total_chunks: number;
  metadata: Record<string, any>;
}

export interface KnowledgeSearchResponse {
  query: string;
  total_results: number;
  chunks: RetrievedChunkItem[];
}
