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
        `Sync complete! ${res.synced_items_count} document(s) updated, ${res.skipped_items_count} unchanged (skipped). Total indexed chunks: ${res.total_chunks}.`
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
      setNotice('Candidate profile updated successfully!');
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
    <section className="integration-card" style={{ marginTop: '1.5rem' }}>
      <div className="card-header">
        <div>
          <h2>Candidate Knowledge Base &amp; RAG</h2>
          <p className="card-subtitle">
            Extracts, chunks, and indexes candidate documents &amp; code into ChromaDB with semantic retrieval.
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={handleSync}
          disabled={syncing || loading}
          style={{ whiteSpace: 'nowrap' }}
        >
          {syncing ? 'Syncing...' : 'Sync Knowledge Base'}
        </button>
      </div>

      {notice && <div className="alert alert-success" style={{ marginTop: '1rem' }}>{notice}</div>}
      {error && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>}

      {/* Sync Status Bar */}
      <div className="source-summary-row" style={{ marginTop: '1rem' }}>
        <div className="source-chip active">
          <strong>Vector Store:</strong> ChromaDB (Local Cosine)
        </div>
        <div className="source-chip active">
          <strong>Embedding Model:</strong> Ollama all-minilm (384d)
        </div>
        {lastSyncResult && (
          <div className="source-chip">
            <strong>Total Chunks:</strong> {lastSyncResult.total_chunks}
          </div>
        )}
        <div className="source-chip">
          <strong>Last Synced:</strong>{' '}
          {profile?.last_synced_at
            ? new Date(profile.last_synced_at).toLocaleString()
            : 'Not yet synced'}
        </div>
      </div>

      {/* Candidate Profile Editor */}
      <div className="discovery-sections">
        <div className="discovery-group">
          <h3>Structured Candidate Intelligence</h3>
          <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem' }}>
            Extracted automatically by the LLM from your uploaded resumes and repositories, editable at any time.
          </p>

          <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.3rem' }}>
                Professional Headline
              </label>
              <input
                type="text"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior Full-Stack Engineer | Python, React, AI"
                style={{
                  width: '100%',
                  padding: '0.6rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.3rem' }}>
                Executive Summary
              </label>
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
                placeholder="Brief summary of your professional expertise and strengths..."
                style={{
                  width: '100%',
                  padding: '0.6rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.3rem' }}>
                Key Skills ({skills.length})
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {skills.map((skill) => (
                  <span
                    key={skill}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      background: '#eff6ff',
                      color: '#1e40af',
                      padding: '0.25rem 0.65rem',
                      borderRadius: '999px',
                      fontSize: '0.825rem',
                      fontWeight: 500,
                    }}
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#6b7280',
                        fontWeight: 'bold',
                      }}
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  placeholder="Add skill (e.g. PostgreSQL, Docker)"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  style={{
                    flex: 1,
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    fontSize: '0.875rem',
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddSkill}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                >
                  Add
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={savingProfile}
              style={{ alignSelf: 'flex-start', marginTop: '0.5rem' }}
            >
              {savingProfile ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </form>
        </div>

        {/* Semantic Retrieval Playground */}
        <div className="discovery-group" style={{ marginTop: '1.5rem', borderTop: '1px solid #e5e7eb', paddingTop: '1.5rem' }}>
          <h3>Semantic Search &amp; RAG Playground</h3>
          <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.85rem' }}>
            Test semantic vector search across your indexed documents. Retrieved chunks include similarity match score and source provenance.
          </p>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. What experience do I have with FastAPI and backend architecture?"
              style={{
                flex: 1,
                padding: '0.6rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '0.875rem',
              }}
            />
            <select
              value={searchLimit}
              onChange={(e) => setSearchLimit(Number(e.target.value))}
              style={{
                padding: '0.6rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '0.875rem',
                backgroundColor: '#ffffff',
              }}
            >
              <option value={2}>Top 2</option>
              <option value={4}>Top 4</option>
              <option value={8}>Top 8</option>
            </select>
            <button
              type="submit"
              className="btn-primary"
              disabled={searching || !searchQuery.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {searching ? 'Searching...' : 'Search Vectors'}
            </button>
          </form>

          {searchResults && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ fontSize: '0.875rem', color: '#4b5563', fontWeight: 600 }}>
                Found {searchResults.total_results} relevant chunk(s) for &ldquo;{searchResults.query}&rdquo;:
              </div>

              {searchResults.chunks.length === 0 ? (
                <div style={{ color: '#6b7280', fontSize: '0.875rem', fontStyle: 'italic' }}>
                  No matching chunks found. Sync your documents first to populate the vector store.
                </div>
              ) : (
                searchResults.chunks.map((chunk: RetrievedChunkItem) => (
                  <div
                    key={chunk.chunk_id}
                    style={{
                      padding: '0.85rem',
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                      background: '#ffffff',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '0.4rem',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span
                          style={{
                            fontSize: '0.725rem',
                            fontWeight: 700,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                            background: chunk.source_type === 'google_drive' ? '#fef3c7' : '#e0f2fe',
                            color: chunk.source_type === 'google_drive' ? '#92400e' : '#075985',
                          }}
                        >
                          {chunk.source_type === 'google_drive' ? 'Drive' : 'GitHub'}
                        </span>
                        <strong style={{ fontSize: '0.875rem' }}>{chunk.title}</strong>
                        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                          Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#059669',
                          background: '#ecfdf5',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '999px',
                        }}
                      >
                        Match: {(chunk.score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <p style={{ fontSize: '0.825rem', color: '#374151', whiteSpace: 'pre-wrap', lineHeight: 1.45 }}>
                      {chunk.content}
                    </p>

                    {chunk.url && (
                      <div style={{ marginTop: '0.4rem' }}>
                        <a
                          href={chunk.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: '0.75rem', color: '#2563eb' }}
                        >
                          View Source &rarr;
                        </a>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
