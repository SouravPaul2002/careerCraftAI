import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ArrowRight } from 'lucide-react';

export function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const isAuthenticated = Boolean(user);

  const handleCtaClick = () => {
    if (isAuthenticated) {
      navigate('/app/chat');
    } else {
      navigate('/register');
    }
  };

  return (
    <div className="canvas-grid" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header
        style={{
          height: '72px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          maxWidth: '1200px',
          width: '100%',
          margin: '0 auto',
          padding: '0 2rem',
        }}
      >
        {/* Brand & Left Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '2.5rem' }}>
          <Link
            to="/"
            style={{
              fontSize: '1.15rem',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: 'var(--text-primary)',
            }}
          >
            CareerCraft
          </Link>
          <nav style={{ display: 'flex', alignItems: 'center', gap: '1.75rem' }}>
            <Link
              to="/app/chat"
              style={{
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                fontWeight: 500,
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
            >
              Workspace
            </Link>
            <Link
              to="/app/knowledge"
              style={{
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                fontWeight: 500,
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
            >
              Knowledge Base
            </Link>
            <Link
              to="/app/studio"
              style={{
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                fontWeight: 500,
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
            >
              LaTeX Studio
            </Link>
          </nav>
        </div>

        {/* Right Auth Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {isAuthenticated ? (
            <Link to="/app/chat" className="btn-pill">
              Open App <ArrowRight size={15} />
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                style={{
                  fontSize: '0.9rem',
                  color: 'var(--text-secondary)',
                  fontWeight: 500,
                  padding: '0.4rem 0.8rem',
                }}
              >
                Sign in
              </Link>
              <Link to="/register" className="btn-pill">
                Get started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4rem 1.5rem 3rem',
          textAlign: 'center',
          maxWidth: '900px',
          margin: '0 auto',
        }}
      >
        {/* Pre-title Label */}
        <div
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            marginBottom: '1.75rem',
            letterSpacing: '-0.01em',
          }}
        >
          CareerCraft — calm ops for job applications
        </div>

        {/* Headline */}
        <h1
          style={{
            fontSize: 'clamp(2.75rem, 6vw, 4.25rem)',
            fontWeight: 800,
            lineHeight: 1.08,
            letterSpacing: '-0.04em',
            color: 'var(--text-primary)',
            marginBottom: '1.5rem',
            maxWidth: '750px',
          }}
        >
          Less noise. More shipped work.
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: 'clamp(1rem, 2vw, 1.1875rem)',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            maxWidth: '600px',
            marginBottom: '2.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          One workspace for plans, handoffs, and automations — built for candidates who care about clarity as much as velocity.
        </p>

        {/* Primary CTA Button */}
        <div>
          <button
            type="button"
            onClick={handleCtaClick}
            className="btn-pill"
            style={{
              padding: '0.75rem 1.75rem',
              fontSize: '1rem',
              fontWeight: 600,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
            }}
          >
            Create your workspace <ArrowRight size={16} />
          </button>
        </div>
      </main>

      {/* Bottom Proof Metrics Bar */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '2.5rem 2rem 3rem',
          maxWidth: '1000px',
          width: '100%',
          margin: '0 auto',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '2rem',
            textAlign: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
              100%
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Evidence grounded
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
              5 Agents
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              LangGraph state machine
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
              99.9%
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              ATS format pass rate
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
              &lt;60s
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Median generation time
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
