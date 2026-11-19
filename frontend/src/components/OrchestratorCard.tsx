import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { runOrchestrator } from '../services/orchestratorService';
import type { OrchestratorRunResponse } from '../types/orchestrator';

export function OrchestratorCard() {
  const { token } = useAuth();

  const [jobRawText, setJobRawText] = useState('');
  const [hintTitle, setHintTitle] = useState('');
  const [hintCompany, setHintCompany] = useState('');

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<OrchestratorRunResponse | null>(null);
  const [error, setError] = useState('');

  async function handleRunOrchestrator() {
    if (!token || !jobRawText.trim()) return;
    setError('');
    setRunning(true);

    try {
      const response = await runOrchestrator(token, {
        job_raw_text: jobRawText,
        hint_title: hintTitle || undefined,
        hint_company: hintCompany || undefined,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Orchestration workflow failed');
    } finally {
      setRunning(false);
    }
  }

  const evaluation = result?.supervisor_evaluation;
  const candidate = result?.candidate_analysis;
  const job = result?.job_analysis;

  // Fit score color helper
  const fitScore = evaluation?.fit_score ?? 0;
  const scoreColor =
    fitScore >= 75 ? '#16a34a' : fitScore >= 50 ? '#d97706' : '#dc2626';
  const scoreBg =
    fitScore >= 75 ? '#dcfce7' : fitScore >= 50 ? '#fef3c7' : '#fee2e2';

  return (
    <section className="card" style={{ marginTop: '1.5rem' }}>
      <div className="card-header">
        <div>
          <h2>Multi-Agent Strategy & Alignment (Phase 5)</h2>
          <p className="card-desc">
            LangGraph orchestrates Job Analysis and Candidate Profile Analysis in parallel, then the Supervisor Agent synthesizes compatibility, detects skill gaps, and formulates application strategy.
          </p>
        </div>
        <span
          className="badge"
          style={{ backgroundColor: '#ede9fe', color: '#5b21b6' }}
        >
          LangGraph Workflow
        </span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ marginTop: '1rem' }}>
        {/* Optional Hints */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            marginBottom: '0.75rem',
          }}
        >
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: '#374151',
                marginBottom: '0.25rem',
              }}
            >
              Target Job Title (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Senior Backend Engineer"
              value={hintTitle}
              onChange={(e) => setHintTitle(e.target.value)}
              disabled={running}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.9rem',
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: '#374151',
                marginBottom: '0.25rem',
              }}
            >
              Hiring Company (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Google, Stripe, etc."
              value={hintCompany}
              onChange={(e) => setHintCompany(e.target.value)}
              disabled={running}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.9rem',
              }}
            />
          </div>
        </div>

        {/* Job Description Textarea */}
        <label
          style={{
            display: 'block',
            fontSize: '0.85rem',
            fontWeight: 600,
            color: '#374151',
            marginBottom: '0.25rem',
          }}
        >
          Job Description Text
        </label>
        <textarea
          rows={6}
          placeholder="Paste full job description text here (minimum 50 characters)..."
          value={jobRawText}
          onChange={(e) => setJobRawText(e.target.value)}
          disabled={running}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.9rem',
            fontFamily: 'inherit',
            resize: 'vertical',
          }}
        />

        {/* Action Button & Run Status */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '0.75rem',
          }}
        >
          <span style={{ fontSize: '0.825rem', color: '#6b7280' }}>
            {jobRawText.trim().length > 0
              ? `${jobRawText.trim().split(/\s+/).length} words · ${jobRawText.trim().length} characters`
              : 'Paste a target job description to run parallel multi-agent evaluation'}
          </span>

          <button
            type="button"
            className="btn-primary"
            onClick={handleRunOrchestrator}
            disabled={running || jobRawText.trim().length < 50}
            style={{
              padding: '0.65rem 1.25rem',
              backgroundColor: '#6366f1',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            {running ? 'Running Multi-Agent Workflow...' : 'Run Alignment & Strategy'}
          </button>
        </div>
      </div>

      {/* Loading Progress State */}
      {running && (
        <div
          style={{
            marginTop: '1.5rem',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ fontWeight: 600, color: '#4338ca', marginBottom: '0.75rem' }}>
            LangGraph Execution in Progress...
          </div>
          <ul
            style={{
              listStyle: 'none',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              fontSize: '0.875rem',
              color: '#475569',
            }}
          >
            <li>Branch 1: Analyzing Job Requirements & Skills...</li>
            <li>Branch 2: Querying Profile & Synthesizing Candidate Strengths...</li>
            <li>Join Node: Supervisor evaluating skill match & strategy...</li>
          </ul>
        </div>
      )}

      {/* Results Section */}
      {result && evaluation && (
        <div
          style={{
            marginTop: '1.75rem',
            borderTop: '1px solid #e5e7eb',
            paddingTop: '1.5rem',
          }}
        >
          {/* Fit Score & Candidate Header */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: '#f9fafb',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              marginBottom: '1.5rem',
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.25rem', color: '#111827', margin: 0 }}>
                {candidate?.headline || 'Candidate Profile'}
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>
                Evaluated against: <strong>{job?.job_title || 'Target Job'}</strong>
                {job?.company_name ? ` at ${job.company_name}` : ''}
              </p>
            </div>

            {/* Score Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: scoreBg,
                color: scoreColor,
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '1.25rem',
              }}
            >
              <span>Fit Score:</span>
              <span>{fitScore}%</span>
            </div>
          </div>

          {/* Candidate Experience Narrative */}
          {candidate?.experience_summary && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: '#374151',
                  marginBottom: '0.25rem',
                }}
              >
                Executive Background Summary
              </label>
              <p
                style={{
                  fontSize: '0.875rem',
                  color: '#4b5563',
                  background: '#f9fafb',
                  padding: '0.75rem',
                  borderRadius: '6px',
                }}
              >
                {candidate.experience_summary}
              </p>
            </div>
          )}

          {/* Matched Skills vs Missing Skills */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            {/* Matched Skills */}
            <div
              style={{
                border: '1px solid #bbf7d0',
                background: '#f0fdf4',
                borderRadius: '8px',
                padding: '1rem',
              }}
            >
              <h4
                style={{
                  fontSize: '0.9rem',
                  color: '#166534',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                }}
              >
                Matched Skills ({evaluation.matched_skills.length})
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {evaluation.matched_skills.length > 0 ? (
                  evaluation.matched_skills.map((skill) => (
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
                  ))
                ) : (
                  <span style={{ fontSize: '0.825rem', color: '#6b7280' }}>
                    No exact matching skills identified.
                  </span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div
              style={{
                border: '1px solid #fecaca',
                background: '#fef2f2',
                borderRadius: '8px',
                padding: '1rem',
              }}
            >
              <h4
                style={{
                  fontSize: '0.9rem',
                  color: '#991b1b',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                }}
              >
                Identified Skill Gaps ({evaluation.missing_skills.length})
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {evaluation.missing_skills.length > 0 ? (
                  evaluation.missing_skills.map((skill) => (
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
                  ))
                ) : (
                  <span style={{ fontSize: '0.825rem', color: '#166534' }}>
                    No critical skill gaps found!
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Strengths & Weaknesses Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            {/* Strengths */}
            <div>
              <h4
                style={{
                  fontSize: '0.9rem',
                  color: '#111827',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                }}
              >
                Key Fit Strengths
              </h4>
              <ul
                style={{
                  paddingLeft: '1.25rem',
                  fontSize: '0.85rem',
                  color: '#374151',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                {evaluation.strengths.map((str, idx) => (
                  <li key={idx}>{str}</li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div>
              <h4
                style={{
                  fontSize: '0.9rem',
                  color: '#111827',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                }}
              >
                Areas to Address
              </h4>
              <ul
                style={{
                  paddingLeft: '1.25rem',
                  fontSize: '0.85rem',
                  color: '#374151',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                {evaluation.weaknesses.map((weak, idx) => (
                  <li key={idx}>{weak}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Strategy Recommendations */}
          <div
            style={{
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <h4
              style={{
                fontSize: '0.95rem',
                color: '#1e293b',
                fontWeight: 700,
                marginBottom: '0.65rem',
              }}
            >
              Actionable Strategy Recommendations (Resume & Application)
            </h4>
            <ol
              style={{
                paddingLeft: '1.25rem',
                fontSize: '0.875rem',
                color: '#334155',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              {evaluation.strategy_recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}
