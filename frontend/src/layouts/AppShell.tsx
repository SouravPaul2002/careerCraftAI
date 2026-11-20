import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  MessageSquare,
  BookOpen,
  Briefcase,
  FileCode,
  Link2,
  LogOut,
  User as UserIcon,
} from 'lucide-react';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { label: 'Chat Assistant', path: '/app/chat', icon: MessageSquare },
    { label: 'Document Studio', path: '/app/studio', icon: FileCode },
    { label: 'Knowledge Base', path: '/app/knowledge', icon: BookOpen },
    { label: 'Jobs Pipeline', path: '/app/jobs', icon: Briefcase },
    { label: 'Integrations', path: '/app/integrations', icon: Link2 },
  ];

  return (
    <div className="canvas-grid" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          height: '64px',
          backgroundColor: 'rgba(248, 247, 243, 0.85)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid var(--border-subtle)',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}
      >
        <div
          style={{
            maxWidth: '1240px',
            height: '100%',
            margin: '0 auto',
            padding: '0 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Brand & Navigation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '2.5rem' }}>
            <Link
              to="/"
              style={{
                fontSize: '1.125rem',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
              }}
            >
              CareerCraft
            </Link>

            <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.45rem 0.85rem',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? 'var(--pill-text)' : 'var(--text-secondary)',
                      backgroundColor: isActive ? 'var(--pill-bg)' : 'transparent',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <Icon size={15} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right User Profile & Logout */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                fontWeight: 500,
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-secondary)',
                }}
              >
                <UserIcon size={14} />
              </div>
              <span>{user?.full_name || user?.email || 'Candidate'}</span>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              title="Sign out"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.4rem 0.75rem',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: 'transparent',
                color: 'var(--text-secondary)',
                fontSize: '0.8125rem',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              <LogOut size={13} />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main style={{ flex: 1, maxWidth: '1240px', width: '100%', margin: '0 auto', padding: '1.5rem' }}>
        {children}
      </main>
    </div>
  );
}
