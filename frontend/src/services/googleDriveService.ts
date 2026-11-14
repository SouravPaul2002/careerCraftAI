import type {
  DriveFilesResponse,
  GoogleConnectionStatus,
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

export async function getGoogleAuthUrl(token: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/google/auth-url`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not start Google connection'));
  }
  const data: { auth_url: string } = await response.json();
  return data.auth_url;
}

export async function getGoogleStatus(token: string): Promise<GoogleConnectionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/google/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not load Google Drive status'));
  }
  return response.json();
}

export async function disconnectGoogleDrive(token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/google/disconnect`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not disconnect Google Drive'));
  }
}

export async function fetchGoogleDriveFiles(token: string): Promise<DriveFilesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/integrations/google/files`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await parseError(response, 'Could not retrieve Google Drive files'));
  }
  return response.json();
}

