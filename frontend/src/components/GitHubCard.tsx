import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  disconnectGitHub,
  fetchGitHubRepoFiles,
  fetchGitHubRepos,
  getGitHubAuthUrl,
  getGitHubStatus,
} from '../services/githubService';
import type {
  GitHubConnectionStatus,
  GitHubRepoFilesResponse,
  GitHubReposResponse,
} from '../types/integration';
import {
  GitBranch,
  RefreshCw,
  LogOut,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';

export function GitHubCard() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [status, setStatus] = useState<GitHubConnectionStatus | null>(null);
  const [reposData, setReposData] = useState<GitHubReposResponse | null>(null);
  const [filesByRepo, setFilesByRepo] = useState<Record<string, GitHubRepoFilesResponse>>({});
  const [inspectingRepo, setInspectingRepo] = useState<string | null>(null);

  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const githubResult = searchParams.get('github');
    if (githubResult === 'connected') {
      setNotice('GitHub connected successfully!');
      setSearchParams({}, { replace: true });
    } else if (githubResult === 'error') {
      const msg = searchParams.get('message') || 'GitHub connection failed.';
      setError(msg);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    async function loadStatus() {
      if (!token) {
        setLoadingStatus(false);
        return;
      }
      try {
        const result = await getGitHubStatus(token);
        setStatus(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check GitHub status');
      } finally {
        setLoadingStatus(false);
      }
    }

    loadStatus();
  }, [token]);

  async function handleConnect() {
    if (!token) return;
    setError('');
    setNotice('');
    try {
      const authUrl = await getGitHubAuthUrl(token);
      window.location.href = authUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start GitHub OAuth');
    }
  }

  async function handleDisconnect() {
    if (!token) return;
    setError('');
    setNotice('');
    try {
      await disconnectGitHub(token);
      setStatus({ connected: false, username: null, scopes: [], connected_at: null });
      setReposData(null);
      setFilesByRepo({});
      setNotice('GitHub disconnected.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not disconnect GitHub');
    }
  }

  async function handleFetchRepos() {
    if (!token) return;
    setError('');
    setLoadingRepos(true);
    try {
      const data = await fetchGitHubRepos(token);
      setReposData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load GitHub repositories');
    } finally {
      setLoadingRepos(false);
    }
  }

  async function handleInspectRepo(owner: string, repoName: string, fullName: string) {
    if (!token) return;
    if (filesByRepo[fullName]) {
      // Toggle closed if already loaded
      setFilesByRepo((prev) => {
        const next = { ...prev };
        delete next[fullName];
        return next;
      });
      return;
    }

    setError('');
    setInspectingRepo(fullName);
    try {
      const result = await fetchGitHubRepoFiles(token, owner, repoName);
      setFilesByRepo((prev) => ({ ...prev, [fullName]: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to inspect ${fullName}`);
    } finally {
      setInspectingRepo(null);
    }
  }

  return (
    <section className="integration-card">
      <div className="integration-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="badge-clean">
              <GitBranch size={13} />
              GitHub
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            GitHub Integration
          </h2>
          <p className="integration-subtitle">
            Public repository access to discover your coding projects, architectural manifests, and documentation.
          </p>
        </div>

        <span className={status?.connected ? 'status-pill connected' : 'status-pill'}>
          {loadingStatus ? (
            'Checking...'
          ) : status?.connected ? (
            <>
              <CheckCircle2 size={12} />
              <span>Connected (@{status.username || 'GitHub'})</span>
            </>
          ) : (
            'Not connected'
          )}
        </span>
      </div>

      {notice && <div className="alert-success">{notice}</div>}
      {error && <div className="alert-error">{error}</div>}

      <div className="integration-actions">
        {!status?.connected ? (
          <button
            type="button"
            className="btn-primary"
            onClick={handleConnect}
            disabled={loadingStatus}
          >
            <GitBranch size={15} />
            <span>Connect GitHub</span>
          </button>
        ) : (
          <>
            <button
              type="button"
              className="btn-primary"
              onClick={handleFetchRepos}
              disabled={loadingRepos}
            >
              <RefreshCw size={14} className={loadingRepos ? 'animate-spin' : ''} />
              <span>{loadingRepos ? 'Fetching Repositories...' : 'Discover Public Repositories'}</span>
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleDisconnect}
            >
              <LogOut size={14} />
              <span>Disconnect</span>
            </button>
          </>
        )}
      </div>

      {reposData && (
        <div className="files-results">
          <div className="files-summary">
            Found <strong>{reposData.total_repos}</strong> public repository(s) (
            <strong>{reposData.relevant_count}</strong> original projects)
          </div>

          {reposData.repos.length === 0 ? (
            <p className="empty-text">
              No public repositories were found on this GitHub account.
            </p>
          ) : (
            <ul className="file-list">
              {reposData.repos.map((repo) => {
                const inspected = filesByRepo[repo.full_name];
                const isInspecting = inspectingRepo === repo.full_name;

                return (
                  <li key={repo.id} className="file-item">
                    <div className="repo-row">
                      <div className="file-main">
                        <div className="file-title-row">
                          {repo.language && (
                            <span className="doc-type-badge">{repo.language}</span>
                          )}
                          <a
                            href={repo.html_url}
                            target="_blank"
                            rel="noreferrer"
                            className="file-name"
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
                          >
                            <span>{repo.full_name}</span>
                            <ExternalLink size={12} style={{ color: 'var(--text-tertiary)' }} />
                          </a>
                          {repo.is_candidate_relevant && (
                            <span className="relevant-badge">Original Project</span>
                          )}
                        </div>
                        {repo.description && (
                          <p className="repo-description">{repo.description}</p>
                        )}
                        <div className="file-meta">
                          <span>{repo.relevance_reason}</span>
                          <span>Stars: {repo.stargazers_count}</span>
                          <span>Forks: {repo.forks_count}</span>
                          <span>
                            Updated:{' '}
                            {repo.updated_at
                              ? new Date(repo.updated_at).toLocaleDateString()
                              : '-'}
                          </span>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="btn-secondary btn-sm"
                        onClick={() =>
                          handleInspectRepo(repo.owner, repo.name, repo.full_name)
                        }
                        disabled={isInspecting}
                      >
                        {isInspecting ? (
                          <>
                            <RefreshCw size={12} className="animate-spin" />
                            <span>Inspecting...</span>
                          </>
                        ) : inspected ? (
                          'Hide Files'
                        ) : (
                          'Inspect Files'
                        )}
                      </button>
                    </div>

                    {inspected && (
                      <div className="repo-files-box">
                        <div className="repo-files-summary">
                          <span>
                            Scanned <strong>{inspected.total_files_scanned}</strong> files ·{' '}
                            <strong>{inspected.relevant_count}</strong> relevant
                          </span>
                          <span>
                            README: <strong>{inspected.has_readme ? 'Yes' : 'No'}</strong>
                          </span>
                          {inspected.manifests.length > 0 && (
                            <span>
                              Manifests: <strong>{inspected.manifests.join(', ')}</strong>
                            </span>
                          )}
                        </div>

                        {inspected.files.length === 0 ? (
                          <p className="empty-text">No relevant files detected.</p>
                        ) : (
                          <ul className="repo-files-list">
                            {inspected.files.slice(0, 20).map((f) => (
                              <li key={f.path} className="repo-file-entry">
                                <span className={`cat-badge cat-${f.category}`}>
                                  {f.category}
                                </span>
                                <code>{f.path}</code>
                              </li>
                            ))}
                            {inspected.files.length > 20 && (
                              <li className="empty-text">
                                ...and {inspected.files.length - 20} more relevant file(s)
                              </li>
                            )}
                          </ul>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

