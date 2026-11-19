import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { resumeOrchestrator, runOrchestrator } from '../services/orchestratorService';
import type { OrchestratorRunResponse } from '../types/orchestrator';

type ActiveTab = 'strategy' | 'resume' | 'cover_letter' | 'judge';

export function OrchestratorCard() {
  const { token } = useAuth();

  const [jobRawText, setJobRawText] = useState('');
  const [hintTitle, setHintTitle] = useState('');
  const [hintCompany, setHintCompany] = useState('');

  const [running, setRunning] = useState(false);
  const [resuming, setResuming] = useState(false);
  const [result, setResult] = useState<OrchestratorRunResponse | null>(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<ActiveTab>('strategy');
  const [copiedNotification, setCopiedNotification] = useState('');

  // Human-in-the-Loop review states
  const [isApprovedByHuman, setIsApprovedByHuman] = useState(false);
  const [showRevisionInput, setShowRevisionInput] = useState(false);
  const [humanFeedback, setHumanFeedback] = useState('');
  const [hitlSuccessMsg, setHitlSuccessMsg] = useState('');

  async function handleRunOrchestrator() {
    if (!token || !jobRawText.trim()) return;
    setError('');
    setHitlSuccessMsg('');
    setIsApprovedByHuman(false);
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

  async function handleApproveApplication() {
    if (!token || !result) return;
    setError('');
    setResuming(true);

    try {
      const response = await resumeOrchestrator(token, {
        thread_id: result.thread_id || 'active',
        action: 'approve',
      });
      setIsApprovedByHuman(true);
      setShowRevisionInput(false);
      setHitlSuccessMsg('Application approved and finalized! Ready for LaTeX & PDF export.');
      setResult((prev) => (prev ? { ...prev, status: response.status } : null));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve application');
    } finally {
      setResuming(false);
    }
  }

  async function handleRequestChanges() {
    if (!token || !result || !humanFeedback.trim()) return;
    setError('');
    setResuming(true);

    try {
      const response = await resumeOrchestrator(token, {
        thread_id: result.thread_id || 'active',
        action: 'request_changes',
        feedback: humanFeedback.trim(),
      });
      setResult(response);
      setHumanFeedback('');
      setShowRevisionInput(false);
      setHitlSuccessMsg('ReAct revision executed! Documents updated based on your feedback.');
      setActiveTab('resume');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request AI revision');
    } finally {
      setResuming(false);
    }
  }

  function handleCopyCoverLetter() {
    const cl = result?.generated_application?.cover_letter;
    if (!cl) return;

    const fullLetter = [
      cl.salutation,
      '',
      cl.opening_paragraph,
      '',
      ...cl.body_paragraphs.map((p) => `${p}\n`),
      cl.closing_paragraph,
      '',
      cl.sign_off,
      result?.generated_application?.resume?.header?.full_name || 'Candidate',
    ].join('\n');

    navigator.clipboard.writeText(fullLetter);
    setCopiedNotification('Cover letter copied to clipboard!');
    setTimeout(() => setCopiedNotification(''), 3000);
  }

  const evaluation = result?.supervisor_evaluation;
  const candidate = result?.candidate_analysis;
  const job = result?.job_analysis;
  const appPackage = result?.generated_application;
  const resume = appPackage?.resume;
  const coverLetter = appPackage?.cover_letter;
  const judge = result?.judge_evaluation;
  const revisionCount = result?.revision_count ?? 0;

  // Fit score color helper
  const fitScore = evaluation?.fit_score ?? 0;
  const scoreColor =
    fitScore >= 75 ? '#16a34a' : fitScore >= 50 ? '#d97706' : '#dc2626';
  const scoreBg =
    fitScore >= 75 ? '#dcfce7' : fitScore >= 50 ? '#fef3c7' : '#fee2e2';

  // Judge decision color helper
  const isApproved = judge?.decision === 'APPROVED';
  const judgeColor = isApproved ? '#16a34a' : '#dc2626';
  const judgeBg = isApproved ? '#dcfce7' : '#fee2e2';

  return (
    <section className="card" style={{ marginTop: '1.5rem' }}>
      <div className="card-header">
        <div>
          <h2>Autonomous Application Pipeline (Phases 5, 7 & 8)</h2>
          <p className="card-desc">
            LangGraph orchestrates Job & Candidate Analysis, generates tailored application documents, and enforces quality control via LLM-as-a-Judge, prompt-injection guardrails, and human review.
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
      {hitlSuccessMsg && <div className="alert alert-success">{hitlSuccessMsg}</div>}

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
              disabled={running || resuming}
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
              disabled={running || resuming}
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
          disabled={running || resuming}
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
              : 'Paste a target job description to run parallel multi-agent evaluation, generation, and quality audit'}
          </span>

          <button
            type="button"
            className="btn-primary"
            onClick={handleRunOrchestrator}
            disabled={running || resuming || jobRawText.trim().length < 50}
            style={{
              padding: '0.65rem 1.25rem',
              backgroundColor: '#6366f1',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            {running ? 'Running End-to-End Pipeline...' : 'Run Application Pipeline'}
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
            <li>Phase 7: Generating Tailored Resume & Authentic Cover Letter...</li>
            <li>Phase 8: LLM-as-a-Judge auditing factual accuracy & ReAct revisions...</li>
          </ul>
        </div>
      )}

      {/* Results Section with HITL Controls & Tabs */}
      {result && evaluation && (
        <div
          style={{
            marginTop: '1.75rem',
            borderTop: '1px solid #e5e7eb',
            paddingTop: '1.5rem',
          }}
        >
          {/* Fit Score & Target Role Header */}
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
              marginBottom: '1rem',
              gap: '0.75rem',
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

            {/* Badges Container */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              {judge && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    background: judgeBg,
                    color: judgeColor,
                    padding: '0.4rem 0.85rem',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '0.95rem',
                  }}
                >
                  <span>Judge:</span>
                  <span>{judge.decision} ({judge.overall_score}%)</span>
                </div>
              )}

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  background: scoreBg,
                  color: scoreColor,
                  padding: '0.4rem 0.85rem',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                }}
              >
                <span>Fit Score:</span>
                <span>{fitScore}%</span>
              </div>
            </div>
          </div>

          {/* HUMAN-IN-THE-LOOP (HITL) APPROVAL & REVISION BAR */}
          <div
            style={{
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px',
              padding: '1rem 1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <div>
                <strong style={{ color: '#166534', fontSize: '0.95rem' }}>
                  {isApprovedByHuman || result.status === 'approved'
                    ? '✓ Application Approved & Finalized'
                    : 'Human Review & Control (Phase 8)'}
                </strong>
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.825rem', color: '#374151' }}>
                  {isApprovedByHuman || result.status === 'approved'
                    ? 'This application version is locked and ready for LaTeX rendering.'
                    : 'Review the tailored documents below. You can approve or prompt the AI for adjustments.'}
                </p>
              </div>

              {!(isApprovedByHuman || result.status === 'approved') && (
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={handleApproveApplication}
                    disabled={resuming}
                    style={{
                      background: '#16a34a',
                      color: '#ffffff',
                      border: 'none',
                      padding: '0.45rem 1rem',
                      borderRadius: '6px',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                    }}
                  >
                    {resuming ? 'Locking...' : '✓ Approve & Finalize'}
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowRevisionInput((prev) => !prev)}
                    disabled={resuming}
                    style={{
                      background: '#ffffff',
                      color: '#4338ca',
                      border: '1px solid #c7d2fe',
                      padding: '0.45rem 1rem',
                      borderRadius: '6px',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                    }}
                  >
                    {showRevisionInput ? 'Cancel Revision' : '✍️ Request AI Revision'}
                  </button>
                </div>
              )}
            </div>

            {/* Expandable Revision Feedback Box */}
            {showRevisionInput && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #dcfce7' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: '#166534', marginBottom: '0.25rem' }}>
                  Describe Specific Changes or Focus Areas:
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    placeholder="e.g. Put more emphasis on Python FastAPI microservices, or remove X project..."
                    value={humanFeedback}
                    onChange={(e) => setHumanFeedback(e.target.value)}
                    disabled={resuming}
                    style={{
                      flex: 1,
                      padding: '0.5rem 0.75rem',
                      border: '1px solid #cbd5e1',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleRequestChanges}
                    disabled={resuming || !humanFeedback.trim()}
                    style={{
                      background: '#4f46e5',
                      color: '#ffffff',
                      border: 'none',
                      padding: '0.5rem 1rem',
                      borderRadius: '6px',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {resuming ? 'Revising...' : 'Submit to AI'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Tab Navigation Header */}
          <div
            style={{
              display: 'flex',
              borderBottom: '2px solid #e5e7eb',
              gap: '0.5rem',
              marginBottom: '1.5rem',
              overflowX: 'auto',
            }}
          >
            <button
              type="button"
              onClick={() => setActiveTab('strategy')}
              style={{
                padding: '0.65rem 1.15rem',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: activeTab === 'strategy' ? '#4f46e5' : '#6b7280',
                borderBottom: activeTab === 'strategy' ? '2px solid #4f46e5' : '2px solid transparent',
                marginBottom: '-2px',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              📊 Match & Strategy
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('resume')}
              style={{
                padding: '0.65rem 1.15rem',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: activeTab === 'resume' ? '#4f46e5' : '#6b7280',
                borderBottom: activeTab === 'resume' ? '2px solid #4f46e5' : '2px solid transparent',
                marginBottom: '-2px',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              📄 Tailored Resume
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('cover_letter')}
              style={{
                padding: '0.65rem 1.15rem',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: activeTab === 'cover_letter' ? '#4f46e5' : '#6b7280',
                borderBottom: activeTab === 'cover_letter' ? '2px solid #4f46e5' : '2px solid transparent',
                marginBottom: '-2px',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              ✉️ Cover Letter
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('judge')}
              style={{
                padding: '0.65rem 1.15rem',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.9rem',
                color: activeTab === 'judge' ? '#4f46e5' : '#6b7280',
                borderBottom: activeTab === 'judge' ? '2px solid #4f46e5' : '2px solid transparent',
                marginBottom: '-2px',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              ⚖️ LLM Judge Audit
            </button>
          </div>

          {/* TAB 1: Match & Strategy */}
          {activeTab === 'strategy' && (
            <div>
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

          {/* TAB 2: Tailored Resume */}
          {activeTab === 'resume' && (
            <div
              style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '1.75rem',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
              }}
            >
              {!resume ? (
                <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                  No resume generated yet. Run the pipeline above to create a tailored resume.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Resume Header */}
                  <div
                    style={{
                      textAlign: 'center',
                      borderBottom: '2px solid #e2e8f0',
                      paddingBottom: '1rem',
                    }}
                  >
                    <h2
                      style={{
                        margin: 0,
                        fontSize: '1.75rem',
                        color: '#0f172a',
                        fontWeight: 700,
                      }}
                    >
                      {resume.header.full_name}
                    </h2>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        justifyContent: 'center',
                        gap: '0.75rem',
                        marginTop: '0.5rem',
                        fontSize: '0.85rem',
                        color: '#475569',
                      }}
                    >
                      {resume.header.email && <span>{resume.header.email}</span>}
                      {resume.header.phone && <span>· {resume.header.phone}</span>}
                      {resume.header.location && <span>· {resume.header.location}</span>}
                      {resume.header.github_url && (
                        <span>
                          ·{' '}
                          <a
                            href={resume.header.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#4f46e5', textDecoration: 'none' }}
                          >
                            GitHub
                          </a>
                        </span>
                      )}
                      {resume.header.linkedin_url && (
                        <span>
                          ·{' '}
                          <a
                            href={resume.header.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#4f46e5', textDecoration: 'none' }}
                          >
                            LinkedIn
                          </a>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Professional Summary */}
                  <div>
                    <h4
                      style={{
                        fontSize: '0.95rem',
                        color: '#1e293b',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        borderBottom: '1px solid #cbd5e1',
                        paddingBottom: '0.35rem',
                        marginBottom: '0.5rem',
                      }}
                    >
                      Professional Summary
                    </h4>
                    <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.6 }}>
                      {resume.professional_summary}
                    </p>
                  </div>

                  {/* Categorized Skills */}
                  <div>
                    <h4
                      style={{
                        fontSize: '0.95rem',
                        color: '#1e293b',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        borderBottom: '1px solid #cbd5e1',
                        paddingBottom: '0.35rem',
                        marginBottom: '0.65rem',
                      }}
                    >
                      Technical Skills
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {Object.entries(resume.skills || {}).map(([category, skillList]) => (
                        <div
                          key={category}
                          style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            alignItems: 'baseline',
                            gap: '0.5rem',
                            fontSize: '0.85rem',
                          }}
                        >
                          <strong style={{ color: '#1e293b', minWidth: '130px' }}>
                            {category}:
                          </strong>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                            {skillList.map((skill) => (
                              <span
                                key={skill}
                                style={{
                                  background: '#f1f5f9',
                                  color: '#334155',
                                  padding: '0.15rem 0.5rem',
                                  borderRadius: '4px',
                                  fontSize: '0.8rem',
                                  border: '1px solid #e2e8f0',
                                }}
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Selected Projects */}
                  {resume.selected_projects && resume.selected_projects.length > 0 && (
                    <div>
                      <h4
                        style={{
                          fontSize: '0.95rem',
                          color: '#1e293b',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          borderBottom: '1px solid #cbd5e1',
                          paddingBottom: '0.35rem',
                          marginBottom: '0.75rem',
                        }}
                      >
                        Selected Relevant Projects
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {resume.selected_projects.map((proj, idx) => (
                          <div key={idx}>
                            <div
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'baseline',
                                marginBottom: '0.25rem',
                              }}
                            >
                              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>
                                {proj.name}
                                {proj.repo_url && (
                                  <a
                                    href={proj.repo_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                      marginLeft: '0.5rem',
                                      fontSize: '0.8rem',
                                      color: '#4f46e5',
                                      textDecoration: 'none',
                                      fontWeight: 500,
                                    }}
                                  >
                                    [View Code]
                                  </a>
                                )}
                              </span>
                              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                                {proj.technologies.join(' · ')}
                              </span>
                            </div>
                            <ul
                              style={{
                                paddingLeft: '1.25rem',
                                fontSize: '0.85rem',
                                color: '#334155',
                                margin: '0.25rem 0 0 0',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.25rem',
                              }}
                            >
                              {proj.bullet_points.map((bp, bpIdx) => (
                                <li key={bpIdx}>{bp}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Work Experience */}
                  {resume.work_experience && resume.work_experience.length > 0 && (
                    <div>
                      <h4
                        style={{
                          fontSize: '0.95rem',
                          color: '#1e293b',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          borderBottom: '1px solid #cbd5e1',
                          paddingBottom: '0.35rem',
                          marginBottom: '0.75rem',
                        }}
                      >
                        Experience & Internships
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {resume.work_experience.map((exp, idx) => (
                          <div key={idx}>
                            <div
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'baseline',
                                marginBottom: '0.25rem',
                              }}
                            >
                              <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>
                                {exp.role} · {exp.company}
                              </strong>
                              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                                {exp.duration} {exp.location ? `| ${exp.location}` : ''}
                              </span>
                            </div>
                            <ul
                              style={{
                                paddingLeft: '1.25rem',
                                fontSize: '0.85rem',
                                color: '#334155',
                                margin: '0.25rem 0 0 0',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.25rem',
                              }}
                            >
                              {exp.bullet_points.map((bp, bpIdx) => (
                                <li key={bpIdx}>{bp}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Education */}
                  {resume.education && resume.education.length > 0 && (
                    <div>
                      <h4
                        style={{
                          fontSize: '0.95rem',
                          color: '#1e293b',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          borderBottom: '1px solid #cbd5e1',
                          paddingBottom: '0.35rem',
                          marginBottom: '0.5rem',
                        }}
                      >
                        Education
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {resume.education.map((edu, idx) => (
                          <div
                            key={idx}
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              fontSize: '0.875rem',
                            }}
                          >
                            <span style={{ color: '#0f172a', fontWeight: 600 }}>
                              {edu.degree} — {edu.institution}
                            </span>
                            <span style={{ color: '#64748b' }}>
                              {edu.year} {edu.grade_or_cgpa ? `(CGPA: ${edu.grade_or_cgpa})` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Tailored Cover Letter */}
          {activeTab === 'cover_letter' && (
            <div
              style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '2rem',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
              }}
            >
              {!coverLetter ? (
                <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                  No cover letter generated yet. Run the pipeline above to generate one.
                </div>
              ) : (
                <div>
                  {/* Action Bar */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '1.5rem',
                      borderBottom: '1px solid #f1f5f9',
                      paddingBottom: '0.75rem',
                    }}
                  >
                    <div>
                      <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                        Target: <strong>{coverLetter.target_role}</strong>
                        {coverLetter.company_name ? ` at ${coverLetter.company_name}` : ''}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {copiedNotification && (
                        <span style={{ fontSize: '0.825rem', color: '#16a34a', fontWeight: 600 }}>
                          ✓ {copiedNotification}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={handleCopyCoverLetter}
                        style={{
                          padding: '0.4rem 0.9rem',
                          background: '#f8fafc',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '0.825rem',
                          fontWeight: 600,
                          color: '#334155',
                        }}
                      >
                        Copy Full Letter
                      </button>
                    </div>
                  </div>

                  {/* Letter Body */}
                  <div
                    style={{
                      fontSize: '0.925rem',
                      lineHeight: 1.7,
                      color: '#1e293b',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '1rem',
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: 600 }}>{coverLetter.salutation}</p>
                    <p style={{ margin: 0 }}>{coverLetter.opening_paragraph}</p>
                    {coverLetter.body_paragraphs.map((para, idx) => (
                      <p key={idx} style={{ margin: 0 }}>
                        {para}
                      </p>
                    ))}
                    <p style={{ margin: 0 }}>{coverLetter.closing_paragraph}</p>
                    <div style={{ marginTop: '1rem' }}>
                      <p style={{ margin: 0 }}>{coverLetter.sign_off}</p>
                      <p style={{ margin: '0.25rem 0 0 0', fontWeight: 700 }}>
                        {resume?.header?.full_name || 'Candidate'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: LLM-as-a-Judge Audit */}
          {activeTab === 'judge' && (
            <div
              style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '1.75rem',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
              }}
            >
              {!judge ? (
                <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                  No judge audit available yet. Run the pipeline above to trigger the LLM Judge.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Verdict Banner */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: judgeBg,
                      border: `1px solid ${isApproved ? '#bbf7d0' : '#fecaca'}`,
                      padding: '1rem 1.25rem',
                      borderRadius: '8px',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: judgeColor, fontWeight: 700 }}>
                        Hiring Committee Evaluation
                      </div>
                      <h3 style={{ margin: '0.25rem 0 0 0', color: judgeColor, fontSize: '1.35rem' }}>
                        Verdict: {judge.decision}
                      </h3>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.35rem', fontWeight: 700, color: judgeColor }}>
                        {judge.overall_score}%
                      </div>
                      <span style={{ fontSize: '0.8rem', color: '#4b5563' }}>
                        {revisionCount > 0 ? `${revisionCount} autonomous ReAct revisions` : 'Direct approval on 1st generation'}
                      </span>
                    </div>
                  </div>

                  {/* 4 Score Cards Grid */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '1rem',
                    }}
                  >
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.85rem' }}>
                      <div style={{ fontSize: '0.775rem', color: '#64748b', fontWeight: 600 }}>Factual Accuracy (40%)</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginTop: '0.25rem' }}>
                        {judge.factual_accuracy_score}%
                      </div>
                    </div>

                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.85rem' }}>
                      <div style={{ fontSize: '0.775rem', color: '#64748b', fontWeight: 600 }}>JD Alignment (25%)</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginTop: '0.25rem' }}>
                        {judge.jd_alignment_score}%
                      </div>
                    </div>

                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.85rem' }}>
                      <div style={{ fontSize: '0.775rem', color: '#64748b', fontWeight: 600 }}>Project Relevance (20%)</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginTop: '0.25rem' }}>
                        {judge.project_relevance_score}%
                      </div>
                    </div>

                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.85rem' }}>
                      <div style={{ fontSize: '0.775rem', color: '#64748b', fontWeight: 600 }}>Readability & Tone (15%)</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginTop: '0.25rem' }}>
                        {judge.readability_score}%
                      </div>
                    </div>
                  </div>

                  {/* Summary Verdict */}
                  <div>
                    <h4 style={{ fontSize: '0.9rem', color: '#1e293b', fontWeight: 700, marginBottom: '0.4rem' }}>
                      Committee Verdict Summary
                    </h4>
                    <p style={{ fontSize: '0.875rem', color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.75rem', borderRadius: '6px', margin: 0, lineHeight: 1.6 }}>
                      {judge.summary_verdict}
                    </p>
                  </div>

                  {/* Unsupported Claims Audit */}
                  <div>
                    <h4 style={{ fontSize: '0.9rem', color: '#1e293b', fontWeight: 700, marginBottom: '0.4rem' }}>
                      Unsupported Claims Audit
                    </h4>
                    {judge.unsupported_claims && judge.unsupported_claims.length > 0 ? (
                      <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#dc2626', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {judge.unsupported_claims.map((claim, idx) => (
                          <li key={idx}>{claim}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ fontSize: '0.85rem', color: '#16a34a', margin: 0, fontWeight: 600 }}>
                        ✓ Zero unsupported claims or hallucinations detected. All bullet points and credentials verified against candidate history.
                      </p>
                    )}
                  </div>

                  {/* Actionable Feedback */}
                  {judge.actionable_feedback && judge.actionable_feedback.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.9rem', color: '#1e293b', fontWeight: 700, marginBottom: '0.4rem' }}>
                        Committee Actionable Feedback
                      </h4>
                      <ol style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#475569', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                        {judge.actionable_feedback.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
