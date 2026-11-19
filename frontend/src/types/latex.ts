/**
 * TypeScript interfaces for the LaTeX & Document Studio API.
 */

export interface TemplateItem {
  id: string;
  name: string;
  description: string;
  category: 'resume' | 'cover_letter';
}

export interface TemplatesResponse {
  resume_templates: TemplateItem[];
  cover_letter_templates: TemplateItem[];
}

export interface RenderLatexRequest {
  application_id: number;
  document_type: 'resume' | 'cover_letter';
  template_name: string;
}

export interface RenderLatexResponse {
  application_id: number;
  document_type: string;
  template_name: string;
  latex_code: string;
  version_number: number;
}

export interface ValidateLatexResponse {
  is_valid: boolean;
  error_message?: string | null;
}

export interface DocumentVersionItem {
  id: number;
  application_id: number;
  document_type: string;
  template_name: string;
  version_number: number;
  latex_content: string;
  is_approved: boolean;
  created_at: string;
}

export interface DocumentVersionsResponse {
  versions: DocumentVersionItem[];
}
