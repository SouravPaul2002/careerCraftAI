/**
 * API service for LaTeX rendering, validation, compilation, and version control.
 */
import type {
  DocumentVersionItem,
  DocumentVersionsResponse,
  RenderLatexRequest,
  RenderLatexResponse,
  TemplatesResponse,
  ValidateLatexResponse,
} from '../types/latex';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseError(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') {
      return data.detail;
    }
  } catch {
    // Ignore JSON parse errors
  }
  return fallback;
}

export async function fetchTemplates(token: string): Promise<TemplatesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/latex/templates`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to fetch LaTeX templates'));
  }
  return response.json();
}

export async function renderLatexDocument(
  token: string,
  payload: RenderLatexRequest
): Promise<RenderLatexResponse> {
  const response = await fetch(`${API_BASE_URL}/api/latex/render`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to render LaTeX document'));
  }
  return response.json();
}

export async function validateLatexCode(
  token: string,
  latexCode: string
): Promise<ValidateLatexResponse> {
  const response = await fetch(`${API_BASE_URL}/api/latex/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ latex_code: latexCode }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to validate LaTeX code'));
  }
  return response.json();
}

export async function compileLatexToPdfBlob(
  token: string,
  latexCode: string
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/latex/compile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ latex_code: latexCode }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to compile LaTeX to PDF'));
  }
  return response.blob();
}

export async function saveDocumentVersion(
  token: string,
  payload: {
    application_id: number;
    document_type: string;
    template_name: string;
    latex_code: string;
    is_approved?: boolean;
  }
): Promise<DocumentVersionItem> {
  const response = await fetch(`${API_BASE_URL}/api/latex/save-version`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to save document version'));
  }
  return response.json();
}

export async function fetchDocumentVersions(
  token: string,
  applicationId: number,
  documentType?: string
): Promise<DocumentVersionsResponse> {
  const url = new URL(`${API_BASE_URL}/api/latex/versions/${applicationId}`);
  if (documentType) {
    url.searchParams.set('document_type', documentType);
  }
  const response = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to fetch document versions'));
  }
  return response.json();
}
