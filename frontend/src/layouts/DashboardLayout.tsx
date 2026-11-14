import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div className="topbar-brand">CareerCraft AI</div>
        <div className="topbar-user">
          <span>
            {user?.full_name} ({user?.email})
          </span>
          <button type="button" className="btn-secondary" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>
      <main className="dashboard-main">{children}</main>
    </div>
  );
}
