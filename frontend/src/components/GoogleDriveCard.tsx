import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  disconnectGoogleDrive,
  fetchGoogleDriveFiles,
  getGoogleAuthUrl,
  getGoogleStatus,
} from '../services/googleDriveService';
import type { DriveFilesResponse, GoogleConnectionStatus } from '../types/integration';
import {
  HardDrive,
  RefreshCw,
  LogOut,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';

function formatFileSize(bytes: number | null): string {
  if (bytes === null) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function GoogleDriveCard() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [status, setStatus] = useState<GoogleConnectionStatus | null>(null);
  const [filesData, setFilesData] = useState<DriveFilesResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const googleResult = searchParams.get('google');
    if (googleResult === 'connected') {
      setNotice('Google Drive connected successfully!');
      setSearchParams({}, { replace: true });
    } else if (googleResult === 'error') {
      const msg = searchParams.get('message') || 'Google Drive connection failed.';
      setError(msg);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    async function loadStatus() {
      if (!token) {
        setLoadingStatus(false);
        return;
      }
      try {
        const result = await getGoogleStatus(token);
        setStatus(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check Google status');
      } finally {
        setLoadingStatus(false);
      }
    }

    loadStatus();
  }, [token]);

  async function handleConnect() {
    if (!token) return;
    setError('');
    setNotice('');
    try {
      const authUrl = await getGoogleAuthUrl(token);
      window.location.href = authUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Google OAuth');
    }
  }

  async function handleDisconnect() {
    if (!token) return;
    setError('');
    setNotice('');
    try {
      await disconnectGoogleDrive(token);
      setStatus({ connected: false, email: null, scopes: [], connected_at: null });
      setFilesData(null);
      setNotice('Google Drive disconnected.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not disconnect Google Drive');
    }
  }

  async function handleFetchFiles() {
    if (!token) return;
    setError('');
    setLoadingFiles(true);
    try {
      const data = await fetchGoogleDriveFiles(token);
      setFilesData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Drive files');
    } finally {
      setLoadingFiles(false);
    }
  }

  return (
    <section className="integration-card">
      <div className="integration-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="badge-clean">
              <HardDrive size={13} />
              Google Drive
            </span>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Google Drive Integration
          </h2>
          <p className="integration-subtitle">
            Read-only access to discover your PDF and DOCX resumes, portfolios, and certifications.
          </p>
        </div>

        <span className={status?.connected ? 'status-pill connected' : 'status-pill'}>
          {loadingStatus ? (
            'Checking...'
          ) : status?.connected ? (
            <>
              <CheckCircle2 size={12} />
              <span>Connected ({status.email || 'Google'})</span>
            </>
          ) : (
            'Not connected'
          )}
        </span>
      </div>

      {notice && <div className="alert-success">{notice}</div>}
      {error && <div className="alert-error">{error}</div>}

      <div className="integration-actions">
        {!status?.connected ? (
          <button
            type="button"
            className="btn-primary"
            onClick={handleConnect}
            disabled={loadingStatus}
          >
            <HardDrive size={15} />
            <span>Connect Google Drive</span>
          </button>
        ) : (
          <>
            <button
              type="button"
              className="btn-primary"
              onClick={handleFetchFiles}
              disabled={loadingFiles}
            >
              <RefreshCw size={14} className={loadingFiles ? 'animate-spin' : ''} />
              <span>{loadingFiles ? 'Scanning Drive...' : 'Discover PDF & DOCX Files'}</span>
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleDisconnect}
            >
              <LogOut size={14} />
              <span>Disconnect</span>
            </button>
          </>
        )}
      </div>

      {filesData && (
        <div className="files-results">
          <div className="files-summary">
            Found <strong>{filesData.total_files}</strong> PDF/DOCX file(s) (
            <strong>{filesData.relevant_count}</strong> matching candidate keywords)
          </div>

          {filesData.files.length === 0 ? (
            <p className="empty-text">
              No PDF or DOCX files were found in this Google Drive account.
            </p>
          ) : (
            <ul className="file-list">
              {filesData.files.map((file) => (
                <li key={file.id} className="file-item">
                  <div className="file-main">
                    <div className="file-title-row">
                      <span className="doc-type-badge">{file.document_type}</span>
                      {file.web_view_link ? (
                        <a
                          href={file.web_view_link}
                          target="_blank"
                          rel="noreferrer"
                          className="file-name"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
                        >
                          <span>{file.name}</span>
                          <ExternalLink size={12} style={{ color: 'var(--text-tertiary)' }} />
                        </a>
                      ) : (
                        <span className="file-name">{file.name}</span>
                      )}
                      {file.is_candidate_relevant && (
                        <span className="relevant-badge">Relevant</span>
                      )}
                    </div>
                    <div className="file-meta">
                      <span>{file.relevance_reason}</span>
                      <span>Size: {formatFileSize(file.size_bytes)}</span>
                      <span>
                        Updated:{' '}
                        {file.modified_time
                          ? new Date(file.modified_time).toLocaleDateString()
                          : '-'}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

