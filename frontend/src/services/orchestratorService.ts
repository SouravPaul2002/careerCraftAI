/**
 * API service for triggering and resuming the LangGraph Multi-Agent Orchestrator.
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

export interface OrchestratorResumeRequest {
  thread_id: string;
  action: 'approve' | 'request_changes';
  feedback?: string;
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

export async function resumeOrchestrator(
  token: string,
  payload: OrchestratorResumeRequest
): Promise<OrchestratorRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/orchestrator/resume`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Failed to resume orchestrator workflow'));
  }

  return response.json();
}

export async function streamOrchestrator(
  token: string,
  payload: OrchestratorRunRequest,
  onEvent: (event: any) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/orchestrator/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Streaming orchestrator failed'));
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No readable stream available');

  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data: ')) {
        try {
          const parsed = JSON.parse(trimmed.slice(6));
          onEvent(parsed);
        } catch {
          // Ignore JSON parse errors for incomplete chunks
        }
      }
    }
  }
}
