import type {
  CandidateProfile,
  CandidateProfileUpdate,
  KnowledgeSearchResponse,
  KnowledgeSyncResponse,
} from '../types/knowledge';

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

export async function syncKnowledgeBase(token: string): Promise<KnowledgeSyncResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/sync`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Knowledge synchronization failed'));
  }
  return response.json();
}

export async function getCandidateProfile(token: string): Promise<CandidateProfile> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to fetch candidate profile'));
  }
  return response.json();
}

export async function updateCandidateProfile(
  token: string,
  payload: CandidateProfileUpdate
): Promise<CandidateProfile> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to update candidate profile'));
  }
  return response.json();
}

export async function searchKnowledgeBase(
  token: string,
  query: string,
  limit: number = 5
): Promise<KnowledgeSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query, limit }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Search failed'));
  }
  return response.json();
}

export async function deleteDocumentChunks(
  token: string,
  externalId: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/documents/${encodeURIComponent(externalId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to delete document'));
  }
  return response.json();
}
