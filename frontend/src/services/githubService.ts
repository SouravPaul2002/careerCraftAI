import type {
  GitHubConnectionStatus,
  GitHubRepoFilesResponse,
  GitHubReposResponse,
} from '../types/integration';

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

export async function getGitHubAuthUrl(token: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/github/auth-url`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not start GitHub connection'));
  }
  const data: { auth_url: string } = await response.json();
  return data.auth_url;
}

export async function getGitHubStatus(token: string): Promise<GitHubConnectionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/github/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not load GitHub status'));
  }
  return response.json();
}

export async function disconnectGitHub(token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/github/disconnect`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not disconnect GitHub'));
  }
}

export async function fetchGitHubRepos(token: string): Promise<GitHubReposResponse> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/github/repos`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not retrieve GitHub repositories'));
  }
  return response.json();
}

export async function fetchGitHubRepoFiles(
  token: string,
  owner: string,
  repo: string
): Promise<GitHubRepoFilesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/integrations/github/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/files`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not inspect repository files'));
  }
  return response.json();
}

