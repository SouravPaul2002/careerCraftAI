import { useLocation } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { DocumentStudioCard } from '../components/DocumentStudioCard';

export function DocumentStudioPage() {
  const location = useLocation();
  const initialAppId = (location.state as { applicationId?: number } | null)?.applicationId;

  return (
    <AppShell>
      <DocumentStudioCard initialApplicationId={initialAppId} />
    </AppShell>
  );
}
