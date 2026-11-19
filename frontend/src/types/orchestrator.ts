/**
 * TypeScript interfaces for the Multi-Agent Orchestrator API.
 */

export interface OrchestratorRunRequest {
  job_raw_text: string;
  hint_title?: string;
  hint_company?: string;
  thread_id?: string;
}

export interface CandidateAnalysisSummary {
  full_name: string;
  headline: string;
  core_skills: string[];
  primary_domains: string[];
  experience_summary?: string | null;
  top_competencies: string[];
}

export interface SupervisorEvaluation {
  fit_score: number;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  strategy_recommendations: string[];
}

export interface ResumeHeader {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
}

export interface ResumeProject {
  name: string;
  technologies: string[];
  bullet_points: string[];
  repo_url?: string | null;
}

export interface ResumeExperience {
  company: string;
  role: string;
  location?: string | null;
  duration?: string | null;
  bullet_points: string[];
}

export interface ResumeEducation {
  degree: string;
  institution: string;
  year?: string | null;
  grade_or_cgpa?: string | null;
}

export interface TailoredResume {
  header: ResumeHeader;
  professional_summary: string;
  skills: Record<string, string[]>;
  selected_projects: ResumeProject[];
  work_experience: ResumeExperience[];
  education: ResumeEducation[];
}

export interface TailoredCoverLetter {
  target_role: string;
  company_name?: string | null;
  salutation: string;
  opening_paragraph: string;
  body_paragraphs: string[];
  closing_paragraph: string;
  sign_off: string;
}

export interface GeneratedApplicationPackage {
  resume: TailoredResume;
  cover_letter: TailoredCoverLetter;
}

export interface JudgeEvaluation {
  decision: 'APPROVED' | 'REJECTED';
  factual_accuracy_score: number;
  jd_alignment_score: number;
  project_relevance_score: number;
  readability_score: number;
  overall_score: number;
  unsupported_claims: string[];
  actionable_feedback: string[];
  summary_verdict: string;
}

export interface OrchestratorRunResponse {
  status: string;
  thread_id?: string;
  job_analysis?: any;
  candidate_profile?: any;
  candidate_analysis?: CandidateAnalysisSummary;
  supervisor_evaluation?: SupervisorEvaluation;
  generated_application?: GeneratedApplicationPackage;
  application_id?: number;
  judge_evaluation?: JudgeEvaluation;
  revision_count?: number;
  errors: string[];
}
