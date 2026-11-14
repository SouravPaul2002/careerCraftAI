import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  getDiscoveredItems,
  runCandidateDiscovery,
  updateDiscoveredItemSelection,
} from '../services/discoveryService';
import type { DiscoveredItem, DiscoveryWorkflowResponse } from '../types/discovery';

function formatProviderName(provider: string): string {
  if (provider === 'google_drive') return 'Google Drive';
  if (provider === 'github') return 'GitHub';
  return provider;
}

export function DiscoveryCard() {
  const { token } = useAuth();

  const [discovery, setDiscovery] = useState<DiscoveryWorkflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadSaved() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await getDiscoveredItems(token);
        setDiscovery(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load discovery');
      } finally {
        setLoading(false);
      }
    }

    loadSaved();
  }, [token]);

  async function handleRunDiscovery() {
    if (!token) return;
    setError('');
    setNotice('');
    setRunning(true);

    try {
      const data = await runCandidateDiscovery(token);
      setDiscovery(data);
      const anyConnected = data.sources.some((s) => s.connected);
      if (!anyConnected) {
        setNotice('Connect Google Drive or GitHub above first, then run discovery.');
      } else {
        setNotice(
          `Discovery finished: ${data.total_items} item(s) collected (${data.selected_count} selected for review).`
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discovery workflow failed');
    } finally {
      setRunning(false);
    }
  }

  async function handleToggle(item: DiscoveredItem) {
    if (!token) return;
    setError('');
    setUpdatingId(item.id);

    try {
      const updated = await updateDiscoveredItemSelection(
        token,
        item.id,
        !item.is_selected
      );
      setDiscovery((prev) => {
        if (!prev) return prev;
        const nextItems = prev.items.map((row) =>
          row.id === updated.id ? updated : row
        );
        return {
          ...prev,
          items: nextItems,
          selected_count: nextItems.filter((row) => row.is_selected).length,
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update selection');
    } finally {
      setUpdatingId(null);
    }
  }

  const driveItems =
    discovery?.items.filter((item) => item.source_type === 'google_drive') ?? [];
  const githubItems =
    discovery?.items.filter((item) => item.source_type === 'github_repo') ?? [];

  return (
    <section className="integration-card">
      <div className="integration-header">
        <div>
          <span className="badge">Phase 2 · Step 3</span>
          <h2>Initial Candidate Data Discovery</h2>
          <p className="integration-subtitle">
            Collect documents &amp; repositories from connected accounts and select what to include in your profile.
          </p>
        </div>

        {discovery && (
          <span className="status-pill connected">
            {discovery.selected_count} / {discovery.total_items} selected
          </span>
        )}
      </div>

      {notice && <div className="alert-success">{notice}</div>}
      {error && <div className="alert-error">{error}</div>}

      {discovery && (
        <div className="source-summary-row">
          {discovery.sources.map((src) => (
            <span
              key={src.provider}
              className={`source-chip ${src.connected ? 'active' : ''}`}
            >
              {formatProviderName(src.provider)}:{' '}
              <strong>
                {src.status === 'not_connected'
                  ? 'Not connected'
                  : src.status === 'error'
                  ? `Error (${src.error || 'failed'})`
                  : `${src.item_count} found`}
              </strong>
            </span>
          ))}
        </div>
      )}

      <div className="integration-actions">
        <button
          type="button"
          className="btn-primary"
          onClick={handleRunDiscovery}
          disabled={loading || running}
        >
          {running ? 'Running Discovery Workflow...' : 'Run Candidate Data Discovery'}
        </button>
      </div>

      {!loading && discovery && discovery.total_items > 0 && (
        <div className="discovery-sections">
          {driveItems.length > 0 && (
            <div className="discovery-group">
              <h3>Google Drive Documents ({driveItems.length})</h3>
              <ul className="file-list">
                {driveItems.map((item) => (
                  <li key={item.id} className="file-item">
                    <label className="discovery-item-row">
                      <input
                        type="checkbox"
                        checked={item.is_selected}
                        disabled={updatingId === item.id}
                        onChange={() => handleToggle(item)}
                      />
                      <div className="file-main">
                        <div className="file-title-row">
                          {item.subtitle && (
                            <span className="doc-type-badge">{item.subtitle}</span>
                          )}
                          {item.url ? (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                              className="file-name"
                            >
                              {item.title}
                            </a>
                          ) : (
                            <span className="file-name">{item.title}</span>
                          )}
                          {item.is_relevant && (
                            <span className="relevant-badge">Relevant</span>
                          )}
                        </div>
                        <div className="file-meta">
                          <span>{item.details.relevance_reason || 'Drive PDF/DOCX'}</span>
                        </div>
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {githubItems.length > 0 && (
            <div className="discovery-group">
              <h3>GitHub Public Repositories ({githubItems.length})</h3>
              <ul className="file-list">
                {githubItems.map((item) => (
                  <li key={item.id} className="file-item">
                    <label className="discovery-item-row">
                      <input
                        type="checkbox"
                        checked={item.is_selected}
                        disabled={updatingId === item.id}
                        onChange={() => handleToggle(item)}
                      />
                      <div className="file-main">
                        <div className="file-title-row">
                          {item.subtitle && (
                            <span className="doc-type-badge">{item.subtitle}</span>
                          )}
                          {item.url ? (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                              className="file-name"
                            >
                              {item.title}
                            </a>
                          ) : (
                            <span className="file-name">{item.title}</span>
                          )}
                          {item.is_relevant && (
                            <span className="relevant-badge">Original Project</span>
                          )}
                        </div>
                        {item.details.description && (
                          <p className="repo-description">{item.details.description}</p>
                        )}
                        <div className="file-meta">
                          <span>{item.details.relevance_reason || 'GitHub repository'}</span>
                          {item.details.has_readme !== undefined && (
                            <span>
                              README: {item.details.has_readme ? 'Yes' : 'No'}
                            </span>
                          )}
                          {Array.isArray(item.details.manifests) &&
                            item.details.manifests.length > 0 && (
                              <span>
                                Manifests: {item.details.manifests.join(', ')}
                              </span>
                            )}
                          {item.details.relevant_files_count !== undefined && (
                            <span>
                              Relevant files: {item.details.relevant_files_count}
                            </span>
                          )}
                        </div>
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

