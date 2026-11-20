import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ChatAssistantPage } from './pages/ChatAssistantPage';
import { DocumentStudioPage } from './pages/DocumentStudioPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { JobsPage } from './pages/JobsPage';
import { IntegrationsPage } from './pages/IntegrationsPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route
            path="/app/chat"
            element={
              <ProtectedRoute>
                <ChatAssistantPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/studio"
            element={
              <ProtectedRoute>
                <DocumentStudioPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/knowledge"
            element={
              <ProtectedRoute>
                <KnowledgePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/jobs"
            element={
              <ProtectedRoute>
                <JobsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/app/integrations"
            element={
              <ProtectedRoute>
                <IntegrationsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/dashboard" element={<Navigate to="/app/chat" replace />} />
          <Route path="/app" element={<Navigate to="/app/chat" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
