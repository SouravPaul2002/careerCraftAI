import type {
  JobAnalysisResponse,
  JobNormalizeResponse,
  JobTextInput,
} from '../types/job';

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

export async function normalizeJobDescription(
  token: string,
  payload: JobTextInput
): Promise<JobNormalizeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/normalize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to normalize job description'));
  }

  return response.json();
}

export async function analyzeJobDescription(
  token: string,
  payload: JobTextInput
): Promise<JobAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to analyze job description'));
  }

  return response.json();
}

