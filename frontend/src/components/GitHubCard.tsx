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
          <span className="badge">Phase 2 · Step 2</span>
          <h2>GitHub Integration</h2>
          <p className="integration-subtitle">
            Public repository access to discover your coding projects, manifests, and READMEs.
          </p>
        </div>

        <span className={status?.connected ? 'status-pill connected' : 'status-pill'}>
          {loadingStatus
            ? 'Checking...'
            : status?.connected
            ? `Connected (@${status.username || 'GitHub'})`
            : 'Not connected'}
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
            Connect GitHub
          </button>
        ) : (
          <>
            <button
              type="button"
              className="btn-primary"
              onClick={handleFetchRepos}
              disabled={loadingRepos}
            >
              {loadingRepos ? 'Fetching Repositories...' : 'Discover Public Repositories'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleDisconnect}
            >
              Disconnect
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
                          >
                            {repo.full_name}
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
                        className="btn-secondary"
                        onClick={() =>
                          handleInspectRepo(repo.owner, repo.name, repo.full_name)
                        }
                        disabled={isInspecting}
                      >
                        {isInspecting
                          ? 'Inspecting...'
                          : inspected
                          ? 'Hide Files'
                          : 'Inspect Files'}
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

