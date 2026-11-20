import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  getCandidateProfile,
  searchKnowledgeBase,
  syncKnowledgeBase,
  updateCandidateProfile,
} from '../services/knowledgeService';
import type {
  CandidateProfile,
  KnowledgeSearchResponse,
  KnowledgeSyncResponse,
  RetrievedChunkItem,
} from '../types/knowledge';
import {
  Database,
  Cpu,
  Layers,
  Clock,
  Search,
  Save,
  Plus,
  X,
  ExternalLink,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

export function KnowledgeBaseCard() {
  const { token } = useAuth();

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<KnowledgeSyncResponse | null>(null);

  // Editable profile state
  const [headline, setHeadline] = useState('');
  const [summary, setSummary] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState('');

  // Semantic search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLimit, setSearchLimit] = useState(4);
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResponse | null>(null);

  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadProfile() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await getCandidateProfile(token);
        setProfile(data);
        setHeadline(data.headline || '');
        setSummary(data.summary || '');
        setSkills(data.skills || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, [token]);

  async function handleSync() {
    if (!token) return;
    setError('');
    setNotice('');
    setSyncing(true);

    try {
      const res = await syncKnowledgeBase(token);
      setLastSyncResult(res);
      setNotice(
        `Sync complete: ${res.synced_items_count} document(s) updated, ${res.skipped_items_count} unchanged (skipped). Total indexed chunks: ${res.total_chunks}.`
      );
      // Reload updated profile
      const updated = await getCandidateProfile(token);
      setProfile(updated);
      setHeadline(updated.headline || '');
      setSummary(updated.summary || '');
      setSkills(updated.skills || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Knowledge sync failed');
    } finally {
      setSyncing(false);
    }
  }

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError('');
    setNotice('');
    setSavingProfile(true);

    try {
      const updated = await updateCandidateProfile(token, {
        headline,
        summary,
        skills,
      });
      setProfile(updated);
      setNotice('Candidate profile updated successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  }

  function handleAddSkill() {
    const trimmed = newSkill.trim();
    if (!trimmed) return;
    if (!skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
    }
    setNewSkill('');
  }

  function handleRemoveSkill(skillToRemove: string) {
    setSkills(skills.filter((s) => s !== skillToRemove));
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !searchQuery.trim()) return;
    setError('');
    setSearching(true);

    try {
      const res = await searchKnowledgeBase(token, searchQuery, searchLimit);
      setSearchResults(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  }

  return (
    <section className="surface-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="badge-clean">
              <Database size={13} />
              RAG &amp; Vector Index
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Candidate Knowledge Base
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.2rem' }}>
            Indexes selected candidate materials into ChromaDB for high-precision semantic retrieval during job matching.
          </p>
        </div>

        <button
          type="button"
          className="btn-pill"
          onClick={handleSync}
          disabled={syncing || loading}
        >
          <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
          <span>{syncing ? 'Syncing index...' : 'Sync Knowledge Base'}</span>
        </button>
      </div>

      {notice && <div className="alert-success">{notice}</div>}
      {error && <div className="alert-error">{error}</div>}

      {/* Sync Status Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
        <div className="chip-clean active">
          <Database size={13} />
          <span>ChromaDB (Local Cosine)</span>
        </div>
        <div className="chip-clean active">
          <Cpu size={13} />
          <span>Embedding: Ollama all-minilm (384d)</span>
        </div>
        {lastSyncResult && (
          <div className="chip-clean">
            <Layers size={13} />
            <span>Indexed chunks: <strong>{lastSyncResult.total_chunks}</strong></span>
          </div>
        )}
        <div className="chip-clean">
          <Clock size={13} />
          <span>
            Last synced:{' '}
            {profile?.last_synced_at
              ? new Date(profile.last_synced_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
              : 'Not yet synced'}
          </span>
        </div>
      </div>

      {/* Structured Candidate Intelligence & Semantic Search */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '1.25rem',
          marginTop: '0.5rem',
        }}
      >
        {/* Panel 1: Structured Candidate Intelligence */}
        <div
          style={{
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Sparkles size={15} style={{ color: 'var(--text-secondary)' }} />
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Candidate Intelligence
              </h3>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Extracted automatically by the LLM from selected resumes and repositories.
            </p>
          </div>

          <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 500, fontSize: '0.8125rem', marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
                Professional Headline
              </label>
              <input
                type="text"
                className="input-clean"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior Full-Stack Engineer | Python, React, Multi-Agent AI"
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 500, fontSize: '0.8125rem', marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
                Executive Summary
              </label>
              <textarea
                className="textarea-clean"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
                placeholder="Brief summary of professional expertise, strengths, and architecture background..."
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label style={{ fontWeight: 500, fontSize: '0.8125rem', color: 'var(--text-primary)' }}>
                  Core Competencies &amp; Skills
                </label>
                <span className="badge-clean">{skills.length} skills</span>
              </div>

              {/* Skills pill container */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.4rem',
                  marginBottom: '0.6rem',
                  maxHeight: '120px',
                  overflowY: 'auto',
                  padding: '0.25rem',
                }}
              >
                {skills.map((skill) => (
                  <span
                    key={skill}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      backgroundColor: 'var(--bg-subtle)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                      padding: '0.2rem 0.6rem',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.7813rem',
                      fontWeight: 500,
                    }}
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                        color: 'var(--text-tertiary)',
                      }}
                      title={`Remove ${skill}`}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>

              {/* Add skill input */}
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  className="input-clean"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  placeholder="Add skill (e.g. LangChain, Docker)"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  className="btn-pill-ghost"
                  onClick={handleAddSkill}
                  style={{ border: '1px solid var(--border-subtle)', padding: '0.45rem 0.85rem' }}
                >
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn-pill"
              disabled={savingProfile}
              style={{ alignSelf: 'flex-start', marginTop: '0.4rem' }}
            >
              <Save size={14} />
              <span>{savingProfile ? 'Saving...' : 'Save Profile'}</span>
            </button>
          </form>
        </div>

        {/* Panel 2: Semantic Retrieval Playground */}
        <div
          style={{
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Search size={15} style={{ color: 'var(--text-secondary)' }} />
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Semantic Search &amp; RAG Playground
              </h3>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Test vector similarity queries against your indexed candidate documents.
            </p>
          </div>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              className="input-clean"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. Experience with microservices or LLM orchestration?"
              style={{ flex: 1 }}
            />
            <select
              className="select-clean"
              value={searchLimit}
              onChange={(e) => setSearchLimit(Number(e.target.value))}
            >
              <option value={2}>Top 2</option>
              <option value={4}>Top 4</option>
              <option value={8}>Top 8</option>
            </select>
            <button
              type="submit"
              className="btn-pill"
              disabled={searching || !searchQuery.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              <Search size={14} />
              <span>{searching ? 'Querying...' : 'Search'}</span>
            </button>
          </form>

          {/* Contained Scroll Results */}
          <div style={{ flex: 1 }}>
            {searchResults && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Found {searchResults.total_results} chunk(s) for &ldquo;{searchResults.query}&rdquo;:
                </div>

                {searchResults.chunks.length === 0 ? (
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', fontStyle: 'italic', padding: '1rem 0' }}>
                    No matching chunks found. Sync your documents first to populate the vector store.
                  </div>
                ) : (
                  <div className="scroll-viewport" style={{ maxHeight: '320px' }}>
                    {searchResults.chunks.map((chunk: RetrievedChunkItem) => (
                      <div
                        key={chunk.chunk_id}
                        className="item-card-row"
                        style={{ flexDirection: 'column', gap: '0.45rem' }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            width: '100%',
                            gap: '0.5rem',
                          }}
                        >
                          <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center', minWidth: 0 }}>
                            <span
                              className={chunk.source_type === 'google_drive' ? 'badge-accent' : 'badge-highlight'}
                            >
                              {chunk.source_type === 'google_drive' ? 'Drive' : 'GitHub'}
                            </span>
                            <strong
                              style={{
                                fontSize: '0.8438rem',
                                color: 'var(--text-primary)',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {chunk.title}
                            </strong>
                            <span style={{ fontSize: '0.7188rem', color: 'var(--text-tertiary)', flexShrink: 0 }}>
                              Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}
                            </span>
                          </div>

                          <span className="badge-success" style={{ flexShrink: 0 }}>
                            {(chunk.score * 100).toFixed(1)}% match
                          </span>
                        </div>

                        <p
                          style={{
                            fontSize: '0.8125rem',
                            color: 'var(--text-secondary)',
                            lineHeight: 1.45,
                            whiteSpace: 'pre-wrap',
                            maxHeight: '80px',
                            overflowY: 'auto',
                            fontFamily: 'var(--font-sans)',
                          }}
                        >
                          {chunk.content}
                        </p>

                        {chunk.url && (
                          <div style={{ alignSelf: 'flex-start' }}>
                            <a
                              href={chunk.url}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.3rem',
                                fontSize: '0.75rem',
                                color: 'var(--text-primary)',
                                fontWeight: 500,
                              }}
                            >
                              <span>View source</span>
                              <ExternalLink size={11} />
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
