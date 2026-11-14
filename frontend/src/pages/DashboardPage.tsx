import { DiscoveryCard } from '../components/DiscoveryCard';
import { GitHubCard } from '../components/GitHubCard';
import { GoogleDriveCard } from '../components/GoogleDriveCard';
import { JobDescriptionCard } from '../components/JobDescriptionCard';
import { KnowledgeBaseCard } from '../components/KnowledgeBaseCard';
import { useAuth } from '../hooks/useAuth';
import { DashboardLayout } from '../layouts/DashboardLayout';

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <section className="welcome-card">
        <h1>Welcome, {user?.full_name}!</h1>
        <p>
          You are signed in to CareerCraft AI. Your account is authenticated
          with JWT and connected to PostgreSQL.
        </p>
        <div className="account-details">
          <div>
            <strong>Email:</strong> {user?.email}
          </div>
          <div>
            <strong>Status:</strong> {user?.is_active ? 'Active' : 'Inactive'}
          </div>
          <div>
            <strong>Member since:</strong>{' '}
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString()
              : '-'}
          </div>
        </div>
      </section>

      <GoogleDriveCard />

      <GitHubCard />

      <DiscoveryCard />

      <KnowledgeBaseCard />

      <JobDescriptionCard />

      <section className="cards-grid" style={{ marginTop: '1.5rem' }}>
        <div className="info-card">
          <span className="badge">Phase 5</span>
          <h3>Multi-Agent Orchestration</h3>
          <p>LangGraph state machine coordinating Job Analysis, Candidate Analysis, and Supervisor.</p>
        </div>

        <div className="info-card">
          <span className="badge">Phase 6</span>
          <h3>MCP Integration</h3>
          <p>Standardized tools for real-time GitHub, Drive, and validation service queries.</p>
        </div>

        <div className="info-card">
          <span className="badge">Phase 7–9</span>
          <h3>Tailored Resume &amp; LaTeX Export</h3>
          <p>Generate tailored resumes and cover letters with HITL review and PDF export.</p>
        </div>
      </section>
    </DashboardLayout>
  );
}
