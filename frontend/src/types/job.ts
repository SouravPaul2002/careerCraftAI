export interface JobTextInput {
  raw_text: string;
  job_title?: string;
  company_name?: string;
}

export interface JobNormalizeResponse {
  cleaned_text: string;
  character_count: number;
  word_count: number;
  is_valid: boolean;
  message: string;
}

export interface JobRequirements {
  minimum_years_experience: number | null;
  education_level: string | null;
}

export interface JobAnalysisOutput {
  job_title: string;
  company_name: string | null;
  role_summary: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  requirements: JobRequirements;
  keywords: string[];
}

export interface JobAnalysisResponse {
  analysis: JobAnalysisOutput;
  raw_text_length: number;
  cleaned_text_length: number;
  analyzed_at: string;
}

