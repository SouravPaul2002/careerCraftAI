import { AppShell } from '../layouts/AppShell';
import { DiscoveryCard } from '../components/DiscoveryCard';
import { KnowledgeBaseCard } from '../components/KnowledgeBaseCard';
import { BookOpen } from 'lucide-react';

export function KnowledgePage() {
  return (
    <AppShell>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingBottom: '3rem' }}>
        {/* Page Editorial Header */}
        <header>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <span className="badge-clean">
              <BookOpen size={13} />
              Candidate ground truth
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Knowledge &amp; Context
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem', marginTop: '0.25rem', maxWidth: '680px' }}>
            Manage discovered documents from Google Drive and repositories from GitHub, index verified materials into ChromaDB, and inspect candidate intelligence.
          </p>
        </header>

        {/* Discovery & Selected Materials */}
        <DiscoveryCard />

        {/* Vector Store & Candidate Profile */}
        <KnowledgeBaseCard />
      </div>
    </AppShell>
  );
}
