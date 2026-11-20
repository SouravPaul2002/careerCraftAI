import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  getDiscoveredItems,
  runCandidateDiscovery,
  updateDiscoveredItemSelection,
} from '../services/discoveryService';
import type { DiscoveredItem, DiscoveryWorkflowResponse } from '../types/discovery';
import {
  HardDrive,
  GitBranch,
  ExternalLink,
  FileText,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  FolderGit2,
  Layers,
  ArrowRight,
} from 'lucide-react';

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
        setNotice('Connect Google Drive or GitHub in Integrations first, then run discovery.');
      } else {
        setNotice(
          `Discovery finished: ${data.total_items} items collected (${data.selected_count} selected for profile sync).`
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

  const driveSelectedCount = driveItems.filter((item) => item.is_selected).length;
  const githubSelectedCount = githubItems.filter((item) => item.is_selected).length;

  return (
    <section className="surface-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="badge-clean">
              <Layers size={13} />
              Candidate discovery
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Discovered Documents &amp; Repositories
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.2rem' }}>
            Review items collected from your cloud accounts and check the ones you want to index into your profile.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {discovery && (
            <span className="badge-highlight">
              {discovery.selected_count} of {discovery.total_items} items selected
            </span>
          )}

          <button
            type="button"
            className="btn-pill"
            onClick={handleRunDiscovery}
            disabled={loading || running}
          >
            {running ? (
              <>
                <RefreshCw size={15} className="animate-spin" />
                <span>Running discovery...</span>
              </>
            ) : (
              <>
                <Sparkles size={15} />
                <span>Run Candidate Discovery</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {notice && <div className="alert-success">{notice}</div>}
      {error && <div className="alert-error">{error}</div>}

      {/* Connected Source Status Row */}
      {discovery && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
          {discovery.sources.map((src) => {
            const isDrive = src.provider === 'google_drive';
            const Icon = isDrive ? HardDrive : GitBranch;
            return (
              <span
                key={src.provider}
                className={`chip-clean ${src.connected ? 'active' : ''}`}
              >
                <Icon size={14} />
                <span>{formatProviderName(src.provider)}:</span>
                <strong style={{ color: src.connected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                  {src.status === 'not_connected'
                    ? 'Not connected'
                    : src.status === 'error'
                    ? `Error (${src.error || 'failed'})`
                    : `${src.item_count} items found`}
                </strong>
                {src.connected ? (
                  <CheckCircle2 size={13} style={{ color: 'var(--accent-success-text)' }} />
                ) : (
                  <AlertCircle size={13} style={{ color: 'var(--text-tertiary)' }} />
                )}
              </span>
            );
          })}
        </div>
      )}

      {/* Two-Column Side-by-Side Contained Scroll Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '1.25rem',
          marginTop: '0.5rem',
        }}
      >
        {/* Card 1: Google Drive Documents */}
        <div
          style={{
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Card Header */}
          <div
            style={{
              padding: '0.85rem 1.15rem',
              borderBottom: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-card)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-primary)',
                }}
              >
                <HardDrive size={16} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Google Drive Documents
                </h3>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge-clean">
                {driveSelectedCount} / {driveItems.length} selected
              </span>
            </div>
          </div>

          {/* Contained Scroll Container */}
          <div style={{ padding: '0.85rem', flex: 1 }}>
            {loading ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 0.5rem auto' }} />
                <p>Loading discovered documents...</p>
              </div>
            ) : driveItems.length === 0 ? (
              <div
                style={{
                  padding: '2.5rem 1rem',
                  textAlign: 'center',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.6rem',
                }}
              >
                <HardDrive size={32} style={{ color: 'var(--text-tertiary)' }} />
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                  No Google Drive files discovered
                </p>
                <p style={{ fontSize: '0.8125rem', maxWidth: '280px', color: 'var(--text-secondary)' }}>
                  Connect your Google Drive account in Integrations, then click Run Candidate Discovery.
                </p>
                <Link
                  to="/app/integrations"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.8125rem',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    marginTop: '0.25rem',
                  }}
                >
                  <span>Go to Integrations</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            ) : (
              <div className="scroll-viewport" style={{ maxHeight: '400px' }}>
                {driveItems.map((item) => (
                  <div
                    key={item.id}
                    className={`item-card-row ${item.is_selected ? 'is-selected' : ''}`}
                    onClick={() => handleToggle(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <input
                      type="checkbox"
                      className="checkbox-clean"
                      checked={item.is_selected}
                      disabled={updatingId === item.id}
                      onChange={() => {}}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.45rem' }}>
                        {item.subtitle && (
                          <span className="badge-accent">{item.subtitle}</span>
                        )}
                        {item.is_relevant && (
                          <span className="badge-success">Relevant</span>
                        )}
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              overflowWrap: 'anywhere',
                            }}
                          >
                            <span>{item.title}</span>
                            <ExternalLink size={12} style={{ color: 'var(--text-tertiary)' }} />
                          </a>
                        ) : (
                          <span
                            style={{
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              overflowWrap: 'anywhere',
                            }}
                          >
                            {item.title}
                          </span>
                        )}
                      </div>

                      <div style={{ fontSize: '0.7813rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        {item.details.relevance_reason || 'Drive document (PDF/DOCX)'}
                      </div>

                      {item.details.size_bytes && (
                        <div style={{ fontSize: '0.7188rem', color: 'var(--text-tertiary)' }}>
                          Size: {(Number(item.details.size_bytes) / 1024).toFixed(1)} KB
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Card 2: GitHub Public Repositories */}
        <div
          style={{
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Card Header */}
          <div
            style={{
              padding: '0.85rem 1.15rem',
              borderBottom: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-card)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-primary)',
                }}
              >
                <GitBranch size={16} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  GitHub Repositories
                </h3>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge-clean">
                {githubSelectedCount} / {githubItems.length} selected
              </span>
            </div>
          </div>

          {/* Contained Scroll Container */}
          <div style={{ padding: '0.85rem', flex: 1 }}>
            {loading ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 0.5rem auto' }} />
                <p>Loading discovered repositories...</p>
              </div>
            ) : githubItems.length === 0 ? (
              <div
                style={{
                  padding: '2.5rem 1rem',
                  textAlign: 'center',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.6rem',
                }}
              >
                <FolderGit2 size={32} style={{ color: 'var(--text-tertiary)' }} />
                <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                  No GitHub repositories discovered
                </p>
                <p style={{ fontSize: '0.8125rem', maxWidth: '280px', color: 'var(--text-secondary)' }}>
                  Connect your GitHub account in Integrations, then click Run Candidate Discovery.
                </p>
                <Link
                  to="/app/integrations"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.8125rem',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    marginTop: '0.25rem',
                  }}
                >
                  <span>Go to Integrations</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            ) : (
              <div className="scroll-viewport" style={{ maxHeight: '400px' }}>
                {githubItems.map((item) => (
                  <div
                    key={item.id}
                    className={`item-card-row ${item.is_selected ? 'is-selected' : ''}`}
                    onClick={() => handleToggle(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <input
                      type="checkbox"
                      className="checkbox-clean"
                      checked={item.is_selected}
                      disabled={updatingId === item.id}
                      onChange={() => {}}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.45rem' }}>
                        {item.subtitle && (
                          <span className="badge-highlight">{item.subtitle}</span>
                        )}
                        {item.is_relevant && (
                          <span className="badge-success">Original Project</span>
                        )}
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              overflowWrap: 'anywhere',
                            }}
                          >
                            <span>{item.title}</span>
                            <ExternalLink size={12} style={{ color: 'var(--text-tertiary)' }} />
                          </a>
                        ) : (
                          <span
                            style={{
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              overflowWrap: 'anywhere',
                            }}
                          >
                            {item.title}
                          </span>
                        )}
                      </div>

                      {item.details.description && (
                        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {item.details.description}
                        </p>
                      )}

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', alignItems: 'center', marginTop: '0.15rem' }}>
                        {item.details.has_readme !== undefined && (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              fontSize: '0.7188rem',
                              color: 'var(--text-tertiary)',
                            }}
                          >
                            <FileText size={11} />
                            README: {item.details.has_readme ? 'Yes' : 'No'}
                          </span>
                        )}

                        {Array.isArray(item.details.manifests) && item.details.manifests.length > 0 && (
                          <span
                            style={{
                              fontSize: '0.7188rem',
                              color: 'var(--text-tertiary)',
                            }}
                          >
                            Manifests: {item.details.manifests.join(', ')}
                          </span>
                        )}

                        {item.details.relevant_files_count !== undefined && (
                          <span
                            style={{
                              fontSize: '0.7188rem',
                              color: 'var(--text-tertiary)',
                            }}
                          >
                            Files: {item.details.relevant_files_count}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
