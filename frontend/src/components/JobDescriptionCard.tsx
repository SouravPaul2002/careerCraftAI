import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { analyzeJobDescription, normalizeJobDescription } from '../services/jobService';
import type { JobAnalysisOutput } from '../types/job';

export function JobDescriptionCard() {
  const { token } = useAuth();

  const [rawText, setRawText] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');

  const [normalizing, setNormalizing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const [stats, setStats] = useState<{ charCount: number; wordCount: number } | null>(null);
  const [analysisResult, setAnalysisResult] = useState<JobAnalysisOutput | null>(null);

  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  async function handleNormalize() {
    if (!token || !rawText.trim()) return;
    setError('');
    setNotice('');
    setNormalizing(true);

    try {
      const res = await normalizeJobDescription(token, {
        raw_text: rawText,
        job_title: jobTitle || undefined,
        company_name: companyName || undefined,
      });

      setRawText(res.cleaned_text);
      setStats({ charCount: res.character_count, wordCount: res.word_count });

      if (res.is_valid) {
        setNotice(`Normalized! Cleaned text has ${res.word_count} words (${res.character_count} characters).`);
      } else {
        setError(res.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Normalization failed');
    } finally {
      setNormalizing(false);
    }
  }

  async function handleAnalyze() {
    if (!token || !rawText.trim()) return;
    setError('');
    setNotice('');
    setAnalyzing(true);

    try {
      const res = await analyzeJobDescription(token, {
        raw_text: rawText,
        job_title: jobTitle || undefined,
        company_name: companyName || undefined,
      });

      setAnalysisResult(res.analysis);
      setNotice(`Job Analysis complete! Extracted ${res.analysis.required_skills.length} required skills and ${res.analysis.responsibilities.length} key responsibilities.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Job analysis failed');
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <section className="integration-card" style={{ marginTop: '1.5rem' }}>
      <div className="card-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h2>Job Description Ingestion &amp; Analysis</h2>
            <span className="badge">Phase 4</span>
          </div>
          <p className="card-subtitle">
            Paste plain-text job postings. The system cleans, normalizes, and extracts structured job requirements.
          </p>
        </div>
      </div>

      {notice && <div className="alert alert-success" style={{ marginTop: '1rem' }}>{notice}</div>}
      {error && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>}

      <div className="discovery-sections" style={{ marginTop: '1rem', borderTop: 'none', paddingTop: 0 }}>
        {/* Optional Hints */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.85rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, marginBottom: '0.25rem' }}>
              Job Title (Optional Hint)
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '0.875rem',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, marginBottom: '0.25rem' }}>
              Company Name (Optional Hint)
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Acme Health"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '0.875rem',
              }}
            />
          </div>
        </div>

        {/* Text Area */}
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.35rem' }}>
            Job Description Text
          </label>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={8}
            placeholder="Paste the complete job description from LinkedIn, Indeed, or career page here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '6px',
              border: '1px solid #d1d5db',
              fontFamily: 'inherit',
              fontSize: '0.875rem',
              lineHeight: 1.5,
            }}
          />
        </div>

        {/* Action Buttons & Word Count */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem' }}>
          <div style={{ fontSize: '0.825rem', color: '#6b7280' }}>
            {stats ? (
              <span>Word count: <strong>{stats.wordCount}</strong> · Characters: <strong>{stats.charCount}</strong></span>
            ) : (
              <span>Paste job description text above to get started</span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={handleNormalize}
              disabled={normalizing || analyzing || !rawText.trim()}
              style={{ backgroundColor: '#4b5563', whiteSpace: 'nowrap' }}
            >
              {normalizing ? 'Cleaning...' : 'Format & Clean'}
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={handleAnalyze}
              disabled={analyzing || !rawText.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {analyzing ? 'Analyzing with Agent...' : 'Analyze Job Description'}
            </button>
          </div>
        </div>

        {/* Structured Analysis Results */}
        {analysisResult && (
          <div style={{ marginTop: '1.5rem', borderTop: '1px solid #e5e7eb', paddingTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: '#111827' }}>{analysisResult.job_title}</h3>
                {analysisResult.company_name && (
                  <span style={{ fontSize: '0.875rem', color: '#4b5563', fontWeight: 500 }}>
                    at {analysisResult.company_name}
                  </span>
                )}
              </div>
              <span className="badge" style={{ backgroundColor: '#ecfdf5', color: '#065f46' }}>
                Analysis Ready
              </span>
            </div>

            {/* Role Summary */}
            {analysisResult.role_summary && (
              <p style={{ fontSize: '0.875rem', color: '#374151', fontStyle: 'italic', marginBottom: '1rem', background: '#f9fafb', padding: '0.65rem', borderRadius: '6px' }}>
                {analysisResult.role_summary}
              </p>
            )}

            {/* Experience / Education Requirements */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
              {analysisResult.requirements.minimum_years_experience !== null && (
                <div style={{ background: '#f3f4f6', padding: '0.35rem 0.65rem', borderRadius: '6px' }}>
                  <strong>Experience:</strong> {analysisResult.requirements.minimum_years_experience}+ years
                </div>
              )}
              {analysisResult.requirements.education_level && (
                <div style={{ background: '#f3f4f6', padding: '0.35rem 0.65rem', borderRadius: '6px' }}>
                  <strong>Education:</strong> {analysisResult.requirements.education_level}
                </div>
              )}
            </div>

            {/* Required Skills */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 700, color: '#991b1b', marginBottom: '0.35rem' }}>
                Required Skills ({analysisResult.required_skills.length})
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {analysisResult.required_skills.map((skill) => (
                  <span
                    key={skill}
                    style={{
                      background: '#fee2e2',
                      color: '#991b1b',
                      fontSize: '0.775rem',
                      fontWeight: 600,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '999px',
                    }}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Preferred Skills */}
            {analysisResult.preferred_skills.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 700, color: '#166534', marginBottom: '0.35rem' }}>
                  Preferred / Bonus Skills ({analysisResult.preferred_skills.length})
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {analysisResult.preferred_skills.map((skill) => (
                    <span
                      key={skill}
                      style={{
                        background: '#dcfce7',
                        color: '#166534',
                        fontSize: '0.775rem',
                        fontWeight: 600,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '999px',
                      }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Responsibilities */}
            {analysisResult.responsibilities.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 700, color: '#1f2937', marginBottom: '0.35rem' }}>
                  Key Responsibilities
                </label>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#374151', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {analysisResult.responsibilities.map((resp, idx) => (
                    <li key={idx}>{resp}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Domain Keywords */}
            {analysisResult.keywords.length > 0 && (
              <div>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 700, color: '#4b5563', marginBottom: '0.35rem' }}>
                  Domain Keywords
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {analysisResult.keywords.map((kw) => (
                    <span
                      key={kw}
                      style={{
                        background: '#f3f4f6',
                        color: '#4b5563',
                        fontSize: '0.75rem',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                      }}
                    >
                      #{kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

