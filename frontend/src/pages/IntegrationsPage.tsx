import { AppShell } from '../layouts/AppShell';
import { GoogleDriveCard } from '../components/GoogleDriveCard';
import { GitHubCard } from '../components/GitHubCard';
import { Link2 } from 'lucide-react';

export function IntegrationsPage() {
  return (
    <AppShell>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingBottom: '3rem' }}>
        <header>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <span className="badge-clean">
              <Link2 size={13} />
              Connected accounts
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Integrations
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem', marginTop: '0.25rem', maxWidth: '680px' }}>
            Connect Google Drive and GitHub via secure OAuth to automatically discover verified resumes, certificates, and code repositories.
          </p>
        </header>

        <GoogleDriveCard />
        <GitHubCard />
      </div>
    </AppShell>
  );
}
