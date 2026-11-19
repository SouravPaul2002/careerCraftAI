import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  compileLatexToPdfBlob,
  fetchDocumentVersions,
  fetchTemplates,
  renderLatexDocument,
  saveDocumentVersion,
  validateLatexCode,
} from '../services/latexService';
import type {
  DocumentVersionItem,
  TemplateItem,
} from '../types/latex';

interface DocumentStudioProps {
  initialApplicationId?: number;
}

export function DocumentStudioCard({ initialApplicationId }: DocumentStudioProps) {
  const { token } = useAuth();

  const [applicationId, setApplicationId] = useState<number>(initialApplicationId || 1);
  const [docType, setDocType] = useState<'resume' | 'cover_letter'>('resume');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('modern');

  const [resumeTemplates, setResumeTemplates] = useState<TemplateItem[]>([]);
  const [coverLetterTemplates, setCoverLetterTemplates] = useState<TemplateItem[]>([]);

  // Workspace View Mode: 'editor' | 'pdf'
  const [activeTab, setActiveTab] = useState<'editor' | 'pdf'>('editor');

  const [latexCode, setLatexCode] = useState<string>('');
  const [validationStatus, setValidationStatus] = useState<{
    valid: boolean;
    message?: string | null;
  } | null>(null);

  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [versionHistory, setVersionHistory] = useState<DocumentVersionItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Sync prop changes
  useEffect(() => {
    if (initialApplicationId) {
      setApplicationId(initialApplicationId);
    }
  }, [initialApplicationId]);

  // Load templates on mount
  useEffect(() => {
    if (!token) return;
    fetchTemplates(token)
      .then((data) => {
        setResumeTemplates(data.resume_templates);
        setCoverLetterTemplates(data.cover_letter_templates);
      })
      .catch((err) => {
        console.error('Failed to load templates', err);
      });
  }, [token]);

  // Load versions whenever application ID or document type changes
  useEffect(() => {
    if (!token || !applicationId) return;
    loadVersions();
  }, [token, applicationId, docType]);

  const loadVersions = async () => {
    if (!token || !applicationId) return;
    try {
      const data = await fetchDocumentVersions(token, applicationId, docType);
      setVersionHistory(data.versions);
    } catch (err: any) {
      console.warn('Could not load version history:', err.message);
    }
  };

  // Render LaTeX from template
  const handleRenderDocument = async (overrideTemplate?: string) => {
    if (!token || !applicationId) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const tmpl = overrideTemplate || selectedTemplate;

    try {
      const result = await renderLatexDocument(token, {
        application_id: applicationId,
        document_type: docType,
        template_name: tmpl,
      });
      setLatexCode(result.latex_code);
      setValidationStatus({ valid: true });
      setSuccessMessage(`Loaded ${docType} in '${tmpl}' template (v${result.version_number})`);
      await loadVersions();
    } catch (err: any) {
      setErrorMessage(err.message || 'Error rendering LaTeX');
    } finally {
      setIsLoading(false);
    }
  };

  // Validate current LaTeX code
  const handleValidate = async () => {
    if (!token || !latexCode) return;
    setErrorMessage(null);
    try {
      const res = await validateLatexCode(token, latexCode);
      setValidationStatus({ valid: res.is_valid, message: res.error_message });
      if (res.is_valid) {
        setSuccessMessage('✓ LaTeX syntax is valid and secure');
      } else {
        setErrorMessage(res.error_message || 'Syntax error in LaTeX');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Validation request failed');
    }
  };

  // Compile LaTeX to PDF Blob and show in embedded viewer
  const handleCompileToPdf = async () => {
    if (!token || !latexCode) return;
    setIsCompiling(true);
    setErrorMessage(null);
    try {
      const blob = await compileLatexToPdfBlob(token, latexCode);
      const url = URL.createObjectURL(blob);
      setPdfBlobUrl(url);
      setActiveTab('pdf');
      setSuccessMessage('✓ Document compiled successfully to PDF');
    } catch (err: any) {
      setErrorMessage(err.message || 'PDF compilation failed');
    } finally {
      setIsCompiling(false);
    }
  };

  // Download raw .tex file
  const handleDownloadTex = () => {
    if (!latexCode) return;
    const blob = new Blob([latexCode], { type: 'text/x-tex' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${docType}_app${applicationId}_${selectedTemplate}.tex`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Download compiled PDF file
  const handleDownloadPdf = async () => {
    if (!token || !latexCode) return;
    setIsCompiling(true);
    setErrorMessage(null);
    try {
      const blob = await compileLatexToPdfBlob(token, latexCode);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${docType}_app${applicationId}_${selectedTemplate}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setSuccessMessage('✓ PDF downloaded successfully');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to download PDF');
    } finally {
      setIsCompiling(false);
    }
  };

  // Save current LaTeX as a new version
  const handleSaveVersion = async (isApproved = false) => {
    if (!token || !applicationId || !latexCode) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const saved = await saveDocumentVersion(token, {
        application_id: applicationId,
        document_type: docType,
        template_name: selectedTemplate,
        latex_code: latexCode,
        is_approved: isApproved,
      });
      setSuccessMessage(
        `✓ Version v${saved.version_number} saved successfully${
          isApproved ? ' (Status: Approved & Finalized)' : ''
        }!`
      );
      await loadVersions();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save version');
    } finally {
      setIsLoading(false);
    }
  };

  // Restore past version into editor
  const handleRestoreVersion = (version: DocumentVersionItem) => {
    setLatexCode(version.latex_content);
    setSelectedTemplate(version.template_name);
    setSuccessMessage(`Restored version v${version.version_number} (${version.template_name})`);
    setValidationStatus({ valid: true });
  };

  const currentTemplateList = docType === 'resume' ? resumeTemplates : coverLetterTemplates;

  return (
    <section className="info-card" style={{ marginTop: '1.5rem', padding: '1.5rem' }}>
      {/* Studio Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span className="badge" style={{ backgroundColor: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0' }}>Phase 9</span>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#0f172a' }}>
              Document Studio &amp; LaTeX PDF Generator
            </h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
            Deterministic Jinja2 LaTeX engine with multi-template selection, code editor, version control, and real-time PDF compilation.
          </p>
        </div>

        {/* Application ID Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Application ID:</label>
          <input
            type="number"
            min={1}
            value={applicationId}
            onChange={(e) => setApplicationId(parseInt(e.target.value) || 1)}
            style={{ width: '70px', padding: '0.35rem 0.5rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
          />
        </div>
      </div>

      {/* Control Bar: Document Type & Template Selection */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', margin: '1rem 0', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        {/* Document Type Switch */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => {
              setDocType('resume');
              setSelectedTemplate('modern');
            }}
            style={{
              padding: '0.45rem 0.9rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: docType === 'resume' ? '1px solid #2563eb' : '1px solid #cbd5e1',
              backgroundColor: docType === 'resume' ? '#2563eb' : '#ffffff',
              color: docType === 'resume' ? '#ffffff' : '#475569',
            }}
          >
            📄 Tailored Resume
          </button>
          <button
            type="button"
            onClick={() => {
              setDocType('cover_letter');
              setSelectedTemplate('formal');
            }}
            style={{
              padding: '0.45rem 0.9rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: docType === 'cover_letter' ? '1px solid #2563eb' : '1px solid #cbd5e1',
              backgroundColor: docType === 'cover_letter' ? '#2563eb' : '#ffffff',
              color: docType === 'cover_letter' ? '#ffffff' : '#475569',
            }}
          >
            ✉️ Cover Letter
          </button>
        </div>

        {/* Template Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Template:</span>
          {currentTemplateList.map((tmpl) => (
            <button
              key={tmpl.id}
              type="button"
              onClick={() => {
                setSelectedTemplate(tmpl.id);
                handleRenderDocument(tmpl.id);
              }}
              title={tmpl.description}
              style={{
                padding: '0.4rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: selectedTemplate === tmpl.id ? 700 : 500,
                cursor: 'pointer',
                border: selectedTemplate === tmpl.id ? '2px solid #0284c7' : '1px solid #cbd5e1',
                backgroundColor: selectedTemplate === tmpl.id ? '#e0f2fe' : '#ffffff',
                color: selectedTemplate === tmpl.id ? '#0369a1' : '#475569',
              }}
            >
              {tmpl.name}
            </button>
          ))}
          <button
            type="button"
            onClick={() => handleRenderDocument()}
            disabled={isLoading}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              backgroundColor: '#f1f5f9',
              color: '#334155',
              border: '1px solid #cbd5e1',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: isLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? '⏳ Rendering...' : '🔄 Load LaTeX'}
          </button>
        </div>
      </div>

      {/* Alert Banners */}
      {errorMessage && (
        <div style={{ padding: '0.75rem 1rem', backgroundColor: '#fef2f2', border: '1px solid #f87171', borderRadius: '6px', color: '#b91c1c', fontSize: '0.875rem', marginBottom: '1rem' }}>
          <strong>Error:</strong> {errorMessage}
        </div>
      )}
      {successMessage && (
        <div style={{ padding: '0.75rem 1rem', backgroundColor: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', color: '#15803d', fontSize: '0.875rem', marginBottom: '1rem' }}>
          {successMessage}
        </div>
      )}

      {/* Main Dual Workspace: Code Editor & Live PDF Viewer */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
        {/* Workspace Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem' }}>
          {/* View Mode Tabs */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setActiveTab('editor')}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: activeTab === 'editor' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'editor' ? '#ffffff' : '#64748b',
              }}
            >
              💻 LaTeX Source Editor
            </button>
            <button
              type="button"
              onClick={() => {
                if (!pdfBlobUrl && latexCode) {
                  handleCompileToPdf();
                } else {
                  setActiveTab('pdf');
                }
              }}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: activeTab === 'pdf' ? '#0f172a' : '#f1f5f9',
                color: activeTab === 'pdf' ? '#ffffff' : '#64748b',
              }}
            >
              👁️ Compiled PDF Viewer
            </button>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={handleValidate}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              🔍 Validate
            </button>
            <button
              type="button"
              onClick={handleCompileToPdf}
              disabled={isCompiling}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: isCompiling ? 'not-allowed' : 'pointer',
              }}
            >
              {isCompiling ? '⚡ Compiling...' : '⚡ Compile PDF'}
            </button>
            <button
              type="button"
              onClick={() => handleSaveVersion(false)}
              disabled={isLoading || !latexCode}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: isLoading ? 'not-allowed' : 'pointer',
              }}
            >
              💾 Save Version
            </button>
            <button
              type="button"
              onClick={handleDownloadTex}
              disabled={!latexCode}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#f8fafc',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: !latexCode ? 'not-allowed' : 'pointer',
              }}
            >
              📥 Download .tex
            </button>
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={isCompiling || !latexCode}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#059669',
                color: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: isCompiling ? 'not-allowed' : 'pointer',
              }}
            >
              📥 Download PDF
            </button>
          </div>
        </div>

        {/* Active Tab Content */}
        {activeTab === 'editor' ? (
          <div>
            <textarea
              value={latexCode}
              onChange={(e) => {
                setLatexCode(e.target.value);
                setValidationStatus(null);
              }}
              placeholder={`Click "🔄 Load LaTeX" above to render your ${docType} into editable LaTeX source code...`}
              rows={22}
              style={{
                width: '100%',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '0.875rem',
                lineHeight: 1.45,
                backgroundColor: '#0f172a',
                color: '#f8fafc',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid #334155',
                resize: 'vertical',
                outline: 'none',
              }}
            />
            {validationStatus && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: validationStatus.valid ? '#16a34a' : '#dc2626' }}>
                {validationStatus.valid ? '✓ LaTeX Syntax Valid' : `✗ Syntax Issue: ${validationStatus.message}`}
              </div>
            )}
          </div>
        ) : (
          <div style={{ height: '560px', backgroundColor: '#f1f5f9', borderRadius: '8px', border: '1px solid #cbd5e1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            {pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                title="Compiled PDF Preview"
                style={{ width: '100%', height: '100%', border: 'none', borderRadius: '8px' }}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#64748b' }}>
                <p style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>No compiled PDF available yet.</p>
                <button
                  type="button"
                  onClick={handleCompileToPdf}
                  disabled={isCompiling || !latexCode}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {isCompiling ? '⚡ Compiling...' : '⚡ Compile Current LaTeX to PDF'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Version History Drawer */}
      <div style={{ marginTop: '1.5rem', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: '0.5rem' }}>
          Document Version History ({versionHistory.length} versions)
        </h3>
        {versionHistory.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            No saved versions for Application #{applicationId} ({docType}). Save a version to track revision snapshots.
          </p>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {versionHistory.map((v) => (
              <div
                key={v.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.4rem 0.75rem',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.825rem',
                }}
              >
                <strong>v{v.version_number}</strong>
                <span style={{ color: '#64748b' }}>({v.template_name})</span>
                {v.is_approved && (
                  <span style={{ backgroundColor: '#dcfce7', color: '#15803d', padding: '0.1rem 0.35rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                    Approved
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => handleRestoreVersion(v)}
                  style={{
                    marginLeft: '0.25rem',
                    padding: '0.15rem 0.4rem',
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  Load
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
