import { useState, useRef, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { AppShell } from '../layouts/AppShell';
import { resumeOrchestrator, streamOrchestrator } from '../services/orchestratorService';
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Sparkles,
  User as UserIcon,
  Bot,
} from 'lucide-react';
import type { GeneratedApplicationPackage, JudgeEvaluation } from '../types/orchestrator';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text?: string;
  // AI Stage Updates & Execution Info
  stages?: {
    node: string;
    message: string;
    completed: boolean;
  }[];
  application?: GeneratedApplicationPackage | null;
  applicationId?: number | null;
  fitScore?: number | null;
  judgeEvaluation?: JudgeEvaluation | null;
  threadId?: string;
  isStreaming?: boolean;
}

export function ChatAssistantPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: "Hello! I am your CareerCraft AI Application Assistant. Paste a job description below, and I will analyze the requirements, match your background, draft a tailored resume with Google XYZ metrics, and audit it with the LLM Judge.",
    },
  ]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTabByMsgId, setActiveTabByMsgId] = useState<Record<string, 'resume' | 'cover_letter' | 'judge'>>({});
  const [revisionFeedback, setRevisionFeedback] = useState<Record<string, string>>({});

  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (event?: FormEvent) => {
    if (event) event.preventDefault();
    if (!inputPrompt.trim() || !token || isProcessing) return;

    const currentText = inputPrompt;
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Append user message
    const newMessages: ChatMessage[] = [
      ...messages,
      {
        id: userMsgId,
        sender: 'user',
        timestamp,
        text: currentText,
      },
      {
        id: assistantMsgId,
        sender: 'assistant',
        timestamp,
        isStreaming: true,
        stages: [
          { node: 'job_analysis', message: 'Analyzing target Job Description...', completed: false },
          { node: 'candidate_analysis', message: 'Retrieving verified profile & skills...', completed: false },
          { node: 'supervisor', message: 'Evaluating fit and tailoring strategy...', completed: false },
          { node: 'application_generation', message: 'Drafting tailored resume & cover letter...', completed: false },
          { node: 'judge', message: 'Auditing factual accuracy with LLM Judge...', completed: false },
        ],
      },
    ];

    setMessages(newMessages);
    setInputPrompt('');
    setIsProcessing(true);

    try {
      await streamOrchestrator(
        token,
        {
          job_raw_text: currentText,
        },
        (chunk) => {
          if (chunk.event === 'stage_update') {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;
                const updatedStages = (msg.stages || []).map((st) => {
                  if (st.node === chunk.node) {
                    return { ...st, message: chunk.message, completed: true };
                  }
                  return st;
                });
                return {
                  ...msg,
                  stages: updatedStages,
                };
              })
            );
          } else if (chunk.event === 'complete') {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;
                return {
                  ...msg,
                  isStreaming: false,
                  application: chunk.application,
                  applicationId: chunk.application_id,
                  fitScore: chunk.fit_score,
                  judgeEvaluation: chunk.decision,
                  text: chunk.application
                    ? `I have successfully analyzed the role and generated a tailored application package. Review the draft below, approve it, or request automated AI revisions.`
                    : 'The multi-agent workflow completed.',
                };
              })
            );
          }
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id !== assistantMsgId) return msg;
          return {
            ...msg,
            isStreaming: false,
            text: `Error during orchestration: ${err.message || 'Unknown error'}`,
          };
        })
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async (threadId?: string) => {
    if (!token || !threadId) return;
    try {
      await resumeOrchestrator(token, {
        thread_id: threadId,
        action: 'approve',
      });
      alert('✓ Application approved and locked! Ready to open in LaTeX Document Studio.');
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleRequestRevision = async (msgId: string, threadId?: string) => {
    const feedback = revisionFeedback[msgId];
    if (!token || !threadId || !feedback?.trim()) {
      alert('Please enter revision feedback first.');
      return;
    }
    setIsProcessing(true);
    try {
      const res = await resumeOrchestrator(token, {
        thread_id: threadId,
        action: 'request_changes',
        feedback,
      });
      // Append revised message
      setMessages((prev) => [
        ...prev,
        {
          id: `revised-${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `Revised application package generated based on your feedback: "${feedback}".`,
          application: res.generated_application,
          applicationId: res.application_id,
          fitScore: res.supervisor_evaluation?.fit_score,
          judgeEvaluation: res.judge_evaluation,
        },
      ]);
    } catch (err: any) {
      alert(`Revision error: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const setMsgTab = (msgId: string, tab: 'resume' | 'cover_letter' | 'judge') => {
    setActiveTabByMsgId((prev) => ({ ...prev, [msgId]: tab }));
  };

  return (
    <AppShell>
      <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', maxWidth: '960px', margin: '0 auto' }}>
        {/* Messages Stream Viewport */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 0', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            const activeTab = activeTabByMsgId[msg.id] || 'resume';

            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  gap: '0.75rem',
                  alignItems: 'flex-start',
                }}
              >
                {/* AI Avatar */}
                {!isUser && (
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--pill-bg)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <Bot size={16} />
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  style={{
                    maxWidth: isUser ? '75%' : '88%',
                    backgroundColor: isUser ? 'var(--pill-bg)' : 'var(--bg-surface)',
                    color: isUser ? '#ffffff' : 'var(--text-primary)',
                    border: isUser ? 'none' : '1px solid var(--border-subtle)',
                    borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    padding: '1.25rem',
                    boxShadow: isUser ? 'none' : '0 2px 10px rgba(0, 0, 0, 0.02)',
                  }}
                >
                  {/* Message Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', fontSize: '0.75rem', color: isUser ? 'rgba(255,255,255,0.7)' : 'var(--text-secondary)' }}>
                    <span style={{ fontWeight: 600 }}>{isUser ? user?.full_name || 'You' : 'CareerCraft Assistant'}</span>
                    <span>{msg.timestamp}</span>
                  </div>

                  {/* Message Text */}
                  {msg.text && (
                    <div style={{ fontSize: '0.9375rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {msg.text}
                    </div>
                  )}

                  {/* Stage Progression Stepper (for AI messages) */}
                  {msg.stages && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Multi-Agent Execution Pipeline
                      </div>
                      {msg.stages.map((st, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem' }}>
                          {st.completed ? (
                            <CheckCircle2 size={14} style={{ color: '#16a34a' }} />
                          ) : (
                            <Clock size={14} style={{ color: 'var(--text-tertiary)' }} />
                          )}
                          <span style={{ color: st.completed ? 'var(--text-primary)' : 'var(--text-tertiary)', fontWeight: st.completed ? 500 : 400 }}>
                            {st.message}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tailored Application Package Tabs */}
                  {msg.application && (
                    <div style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
                      {/* Tabs Bar */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.35rem' }}>
                          <button
                            type="button"
                            onClick={() => setMsgTab(msg.id, 'resume')}
                            style={{
                              padding: '0.35rem 0.75rem',
                              borderRadius: 'var(--radius-full)',
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              border: '1px solid var(--border-subtle)',
                              backgroundColor: activeTab === 'resume' ? 'var(--pill-bg)' : 'transparent',
                              color: activeTab === 'resume' ? '#ffffff' : 'var(--text-secondary)',
                            }}
                          >
                            📄 Tailored Resume
                          </button>
                          <button
                            type="button"
                            onClick={() => setMsgTab(msg.id, 'cover_letter')}
                            style={{
                              padding: '0.35rem 0.75rem',
                              borderRadius: 'var(--radius-full)',
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              border: '1px solid var(--border-subtle)',
                              backgroundColor: activeTab === 'cover_letter' ? 'var(--pill-bg)' : 'transparent',
                              color: activeTab === 'cover_letter' ? '#ffffff' : 'var(--text-secondary)',
                            }}
                          >
                            ✉️ Cover Letter
                          </button>
                        </div>

                        {/* Open in Studio Action */}
                        {msg.applicationId && (
                          <button
                            type="button"
                            onClick={() => navigate('/app/studio', { state: { applicationId: msg.applicationId } })}
                            className="btn-pill"
                            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8125rem' }}
                          >
                            Open in LaTeX Studio <ExternalLink size={12} />
                          </button>
                        )}
                      </div>

                      {/* Tab Content: Resume */}
                      {activeTab === 'resume' && (
                        <div style={{ background: '#FAF9F5', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.25rem' }}>{msg.application.resume.header.full_name}</h4>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>{msg.application.resume.professional_summary}</p>
                          <div style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.25rem' }}>Work Experience</div>
                          {msg.application.resume.work_experience.map((exp, idx) => (
                            <div key={idx} style={{ marginBottom: '0.5rem', fontSize: '0.8125rem' }}>
                              <strong>{exp.role}</strong> at <em>{exp.company}</em> ({exp.duration})
                              <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                                {exp.bullet_points.map((bp, bidx) => (
                                  <li key={bidx}>{bp}</li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Tab Content: Cover Letter */}
                      {activeTab === 'cover_letter' && (
                        <div style={{ background: '#FAF9F5', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.875rem', lineHeight: 1.6 }}>
                          <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{msg.application.cover_letter.salutation}</p>
                          <p style={{ marginBottom: '0.5rem' }}>{msg.application.cover_letter.opening_paragraph}</p>
                          {msg.application.cover_letter.body_paragraphs.map((p, pidx) => (
                            <p key={pidx} style={{ marginBottom: '0.5rem' }}>{p}</p>
                          ))}
                          <p style={{ marginTop: '0.75rem' }}>{msg.application.cover_letter.sign_off}<br /><strong>{msg.application.resume.header.full_name}</strong></p>
                        </div>
                      )}

                      {/* Action Bar */}
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          onClick={() => handleApprove(msg.threadId)}
                          style={{
                            padding: '0.45rem 1rem',
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: '#16a34a',
                            color: '#ffffff',
                            border: 'none',
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          ✓ Approve Application
                        </button>

                        <div style={{ display: 'flex', gap: '0.35rem', flex: 1, minWidth: '220px' }}>
                          <input
                            type="text"
                            placeholder="Request specific revisions (e.g. emphasize PostgreSQL)..."
                            value={revisionFeedback[msg.id] || ''}
                            onChange={(e) => setRevisionFeedback(prev => ({ ...prev, [msg.id]: e.target.value }))}
                            style={{
                              flex: 1,
                              padding: '0.4rem 0.75rem',
                              borderRadius: 'var(--radius-full)',
                              border: '1px solid var(--border-subtle)',
                              fontSize: '0.8125rem',
                              backgroundColor: '#FAF9F5',
                              color: 'var(--text-primary)',
                              outline: 'none',
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => handleRequestRevision(msg.id, msg.threadId)}
                            disabled={isProcessing || !revisionFeedback[msg.id]?.trim()}
                            className="btn-pill"
                            style={{ padding: '0.4rem 0.85rem', fontSize: '0.8125rem' }}
                          >
                            Revise
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* User Avatar */}
                {isUser && (
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--border-subtle)',
                      color: 'var(--text-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <UserIcon size={16} />
                  </div>
                )}
              </div>
            );
          })}
          <div ref={chatEndRef} />
        </div>

        {/* Suggested Prompts Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
          <button
            type="button"
            onClick={() => setInputPrompt("Role: Senior Python Developer\nCompany: Stripe\nRequirements:\n- 5+ years experience in Python and FastAPI\n- Multi-agent or LLM orchestration\n- PostgreSQL and distributed systems")}
            className="badge-clean"
            style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}
          >
            <Sparkles size={11} /> Sample Senior Python Role
          </button>
          <button
            type="button"
            onClick={() => setInputPrompt("Role: Staff Frontend Engineer\nCompany: Vercel\nRequirements:\n- TypeScript, React 18, Vite\n- Design systems, clean state management\n- Performance optimization")}
            className="badge-clean"
            style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}
          >
            <Sparkles size={11} /> Sample Staff Frontend Role
          </button>
        </div>

        {/* Bottom Floating Prompt Input Bar */}
        <form
          onSubmit={handleSendMessage}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '0.65rem 0.85rem',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
          }}
        >
          <textarea
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Paste a target job description or prompt to generate/revise applications... (Shift+Enter for new line)"
            rows={2}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontFamily: 'inherit',
              fontSize: '0.9375rem',
              backgroundColor: 'transparent',
              color: 'var(--text-primary)',
            }}
          />

          <button
            type="submit"
            disabled={isProcessing || !inputPrompt.trim()}
            className="btn-pill"
            style={{
              padding: '0.6rem 1rem',
              borderRadius: 'var(--radius-full)',
              opacity: isProcessing || !inputPrompt.trim() ? 0.4 : 1,
              cursor: isProcessing || !inputPrompt.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            <span>{isProcessing ? 'Thinking...' : 'Send'}</span>
            <ArrowRight size={15} />
          </button>
        </form>
      </div>
    </AppShell>
  );
}
