import type { DiscoveredItem, DiscoveryWorkflowResponse } from '../types/discovery';

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

export async function getDiscoveredItems(
  token: string
): Promise<DiscoveryWorkflowResponse> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/items`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not load discovered items'));
  }
  return response.json();
}

export async function runCandidateDiscovery(
  token: string
): Promise<DiscoveryWorkflowResponse> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/run`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Candidate discovery failed'));
  }
  return response.json();
}

export async function updateDiscoveredItemSelection(
  token: string,
  itemId: number,
  isSelected: boolean
): Promise<DiscoveredItem> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/items/${itemId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_selected: isSelected }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not update selection'));
  }
  return response.json();
}

