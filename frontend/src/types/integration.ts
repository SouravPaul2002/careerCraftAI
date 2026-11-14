export interface GoogleConnectionStatus {
  connected: boolean;
  email: string | null;
  scopes: string[];
  connected_at: string | null;
}

export interface DriveFileItem {
  id: string;
  name: string;
  mime_type: string;
  document_type: string;
  size_bytes: number | null;
  modified_time: string | null;
  web_view_link: string | null;
  is_candidate_relevant: boolean;
  relevance_reason: string;
}

export interface DriveFilesResponse {
  total_files: number;
  relevant_count: number;
  files: DriveFileItem[];
}

export interface GitHubConnectionStatus {
  connected: boolean;
  username: string | null;
  scopes: string[];
  connected_at: string | null;
}

export interface GitHubRepoItem {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  description: string | null;
  html_url: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  topics: string[];
  is_fork: boolean;
  default_branch: string;
  updated_at: string | null;
  is_candidate_relevant: boolean;
  relevance_reason: string;
}

export interface GitHubReposResponse {
  total_repos: number;
  relevant_count: number;
  repos: GitHubRepoItem[];
}

export interface GitHubFileItem {
  path: string;
  category: 'documentation' | 'manifest' | 'source';
  size_bytes: number | null;
}

export interface GitHubRepoFilesResponse {
  repo_full_name: string;
  default_branch: string;
  total_files_scanned: number;
  relevant_count: number;
  has_readme: boolean;
  manifests: string[];
  files: GitHubFileItem[];
}
