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

export interface OrchestratorRunResponse {
  status: string;
  thread_id?: string;
  job_analysis?: any;
  candidate_profile?: any;
  candidate_analysis?: CandidateAnalysisSummary;
  supervisor_evaluation?: SupervisorEvaluation;
  errors: string[];
}
