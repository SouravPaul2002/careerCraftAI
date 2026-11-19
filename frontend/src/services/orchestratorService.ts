/**
 * API service for triggering the LangGraph Multi-Agent Orchestrator.
 */
import type { OrchestratorRunRequest, OrchestratorRunResponse } from '../types/orchestrator';

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

export async function runOrchestrator(
  token: string,
  payload: OrchestratorRunRequest
): Promise<OrchestratorRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/orchestrator/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to run multi-agent orchestrator'));
  }

  return response.json();
}
